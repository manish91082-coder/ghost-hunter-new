// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface IERC20Phase19 {
    function approve(address spender, uint256 amount) external returns (bool);
    function balanceOf(address account) external view returns (uint256);
    function transfer(address to, uint256 amount) external returns (bool);
}

interface IAaveV3PoolPhase19 {
    function flashLoanSimple(
        address receiverAddress,
        address asset,
        uint256 amount,
        bytes calldata params,
        uint16 referralCode
    ) external;
}

interface IQuickSwapV2RouterPhase19 {
    function swapExactTokensForTokens(
        uint256 amountIn,
        uint256 amountOutMin,
        address[] calldata path,
        address to,
        uint256 deadline
    ) external returns (uint256[] memory amounts);
}

interface IUniswapV3RouterPhase19 {
    struct ExactInputSingleParams {
        address tokenIn;
        address tokenOut;
        uint24 fee;
        address recipient;
        uint256 deadline;
        uint256 amountIn;
        uint256 amountOutMinimum;
        uint160 sqrtPriceLimitX96;
    }

    function exactInputSingle(ExactInputSingleParams calldata params) external returns (uint256 amountOut);
}

/// @notice Minimal Phase-19 execution sink for the first two-leg Aave V3 strategy.
/// @dev Off-chain Governor/Signer/PrivateSubmit remain authoritative for authorization.
///      This contract independently enforces caller, Aave callback, route commitment,
///      per-leg minimums, deadline, repayment, replay protection, and a token-denominated
///      minimum surplus. It deliberately never attempts USD valuation on-chain.
contract Phase19Executor {
    error Unauthorized();
    error InvalidAddress();
    error InvalidAmount();
    error InvalidDeadline();
    error InvalidRoute();
    error InvalidCaller();
    error InvalidInitiator();
    error InvalidAsset();
    error InvalidLoanAmount();
    error MinimumOutputFailed();
    error RepaymentFailed();
    error MinimumSurplusFailed();
    error TransferFailed();
    error ApprovalFailed();
    error Reentrancy();
    error IntentAlreadyConsumed();

    address public immutable owner;
    address public immutable aavePool;
    address public immutable quickSwapRouter;
    address public immutable uniswapV3Router;

    uint256 private constant NOT_ENTERED = 1;
    uint256 private constant ENTERED = 2;
    uint256 private _status = NOT_ENTERED;

    mapping(bytes32 => bool) public consumedIntent;

    struct ExecutionParams {
        address asset;
        address tokenMid;
        bool firstOnQuickSwap;
        uint24 uniswapFee;
        uint256 amountOutMinFirst;
        uint256 amountOutMinSecond;
        uint256 minimumSurplus;
        uint256 deadline;
        bytes32 routeHash;
        bytes32 intentHash;
    }

    event ExecutionSettled(
        bytes32 indexed intentHash,
        bytes32 indexed routeHash,
        address indexed asset,
        uint256 loanAmount,
        uint256 premium,
        uint256 finalBalance,
        uint256 realizedTokenSurplus
    );

    constructor(address aavePool_, address quickSwapRouter_, address uniswapV3Router_) {
        if (aavePool_ == address(0) || quickSwapRouter_ == address(0) || uniswapV3Router_ == address(0)) {
            revert InvalidAddress();
        }
        owner = msg.sender;
        aavePool = aavePool_;
        quickSwapRouter = quickSwapRouter_;
        uniswapV3Router = uniswapV3Router_;
    }

    modifier onlyOwner() {
        if (msg.sender != owner) revert Unauthorized();
        _;
    }

    modifier nonReentrant() {
        if (_status == ENTERED) revert Reentrancy();
        _status = ENTERED;
        _;
        _status = NOT_ENTERED;
    }

    /// @notice Canonical on-chain route commitment used by ExecutionParams.routeHash.
    ///         Economics, deadlines and minimum outputs are intentionally excluded from
    ///         this topology hash because they are separate execution constraints.
    function routeHash(
        address asset,
        address tokenMid,
        bool firstOnQuickSwap,
        uint24 uniswapFee
    ) public view returns (bytes32) {
        if (asset == address(0) || tokenMid == address(0) || uniswapFee == 0) revert InvalidRoute();
        return keccak256(abi.encode(
            asset,
            tokenMid,
            firstOnQuickSwap,
            uniswapFee,
            aavePool,
            quickSwapRouter,
            uniswapV3Router
        ));
    }

    /// @notice Starts one Aave V3 flash-loan execution.
    /// @dev The signed transaction must bind the complete calldata including params.
    function execute(ExecutionParams calldata p, uint256 amount) external onlyOwner {
        if (p.asset == address(0) || p.tokenMid == address(0)) revert InvalidAddress();
        if (amount == 0) revert InvalidAmount();
        if (p.deadline < block.timestamp) revert InvalidDeadline();
        if (p.amountOutMinFirst == 0 || p.amountOutMinSecond == 0) revert InvalidAmount();
        if (p.routeHash != routeHash(p.asset, p.tokenMid, p.firstOnQuickSwap, p.uniswapFee)) {
            revert InvalidRoute();
        }
        if (p.intentHash == bytes32(0) || consumedIntent[p.intentHash]) revert InvalidRoute();
        if (p.minimumSurplus == 0) revert InvalidAmount();

        bytes memory encoded = abi.encode(p, amount);
        IAaveV3PoolPhase19(aavePool).flashLoanSimple(address(this), p.asset, amount, encoded, 0);
    }

    /// @notice Aave V3 callback. Only the configured pool and this contract's own
    ///         flash-loan initiation may reach this function.
    function executeOperation(
        address asset,
        uint256 amount,
        uint256 premium,
        address initiator,
        bytes calldata encodedParams
    ) external nonReentrant returns (bool) {
        if (msg.sender != aavePool) revert InvalidCaller();
        if (initiator != address(this)) revert InvalidInitiator();

        ExecutionParams memory p = abi.decode(encodedParams, (ExecutionParams));
        if (asset != p.asset) revert InvalidAsset();
        if (amount == 0) revert InvalidLoanAmount();
        if (p.deadline < block.timestamp) revert InvalidDeadline();
        if (p.tokenMid == address(0) || p.intentHash == bytes32(0)) revert InvalidRoute();
        if (p.routeHash != routeHash(p.asset, p.tokenMid, p.firstOnQuickSwap, p.uniswapFee)) {
            revert InvalidRoute();
        }
        if (consumedIntent[p.intentHash]) revert IntentAlreadyConsumed();

        uint256 balanceBefore = IERC20Phase19(asset).balanceOf(address(this));
        if (balanceBefore < amount) revert InvalidLoanAmount();

        if (p.firstOnQuickSwap) {
            uint256 midAmount = _swapQuickSwap(asset, p.tokenMid, amount, p.amountOutMinFirst, p.deadline);
            _swapUniswap(p.tokenMid, asset, midAmount, p.uniswapFee, p.amountOutMinSecond, p.deadline);
        } else {
            uint256 midAmount = _swapUniswap(asset, p.tokenMid, amount, p.uniswapFee, p.amountOutMinFirst, p.deadline);
            _swapQuickSwap(p.tokenMid, asset, midAmount, p.amountOutMinSecond, p.deadline);
        }

        uint256 balanceAfter = IERC20Phase19(asset).balanceOf(address(this));
        uint256 repayment = amount + premium;
        if (balanceAfter < repayment) revert RepaymentFailed();
        if (balanceAfter < repayment + p.minimumSurplus) revert MinimumSurplusFailed();

        if (!IERC20Phase19(asset).approve(aavePool, repayment)) revert ApprovalFailed();
        consumedIntent[p.intentHash] = true;

        emit ExecutionSettled(
            p.intentHash,
            p.routeHash,
            asset,
            amount,
            premium,
            balanceAfter,
            balanceAfter - repayment
        );
        return true;
    }

    function _approveExact(address token, address spender, uint256 amount) internal {
        // Reset first for tokens that require zero-before-nonzero approvals.
        if (!IERC20Phase19(token).approve(spender, 0)) revert ApprovalFailed();
        if (!IERC20Phase19(token).approve(spender, amount)) revert ApprovalFailed();
    }

    function _resetApproval(address token, address spender) internal {
        if (!IERC20Phase19(token).approve(spender, 0)) revert ApprovalFailed();
    }

    function _swapQuickSwap(
        address tokenIn,
        address tokenOut,
        uint256 amountIn,
        uint256 amountOutMin,
        uint256 deadline
    ) internal returns (uint256 amountOut) {
        _approveExact(tokenIn, quickSwapRouter, amountIn);
        address[] memory path = new address[](2);
        path[0] = tokenIn;
        path[1] = tokenOut;
        uint256[] memory amounts = IQuickSwapV2RouterPhase19(quickSwapRouter).swapExactTokensForTokens(
            amountIn,
            amountOutMin,
            path,
            address(this),
            deadline
        );
        _resetApproval(tokenIn, quickSwapRouter);
        if (amounts.length < 2 || amounts[amounts.length - 1] < amountOutMin) revert MinimumOutputFailed();
        return amounts[amounts.length - 1];
    }

    function _swapUniswap(
        address tokenIn,
        address tokenOut,
        uint256 amountIn,
        uint24 fee,
        uint256 amountOutMin,
        uint256 deadline
    ) internal returns (uint256 amountOut) {
        if (fee == 0) revert InvalidAmount();
        _approveExact(tokenIn, uniswapV3Router, amountIn);
        amountOut = IUniswapV3RouterPhase19(uniswapV3Router).exactInputSingle(
            IUniswapV3RouterPhase19.ExactInputSingleParams({
                tokenIn: tokenIn,
                tokenOut: tokenOut,
                fee: fee,
                recipient: address(this),
                deadline: deadline,
                amountIn: amountIn,
                amountOutMinimum: amountOutMin,
                sqrtPriceLimitX96: 0
            })
        );
        _resetApproval(tokenIn, uniswapV3Router);
        if (amountOut < amountOutMin) revert MinimumOutputFailed();
    }

    function withdraw(address token, uint256 amount) external onlyOwner nonReentrant {
        if (token == address(0) || amount == 0) revert InvalidAmount();
        if (!IERC20Phase19(token).transfer(owner, amount)) revert TransferFailed();
    }
}
