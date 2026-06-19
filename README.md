# Thales Trading Bot
> It's much better to be convex than to be right.

---

# 泰利斯交易机器人
> 凸性远比正确更重要。


Step	What it does	Covered by the 3 tests?
1. Compute DTE per expiry	expiry code → days	Test 1 ✅
2. Pick ATM strike per expiry	strike list + spot → ATM + window	Test 2 ✅
3. Read call/put IV at ATM, average	per-strike IV → atmIv per expiry	(glue)
4. Fold into tenor buckets	per-expiry rows → (1D…6M, atmIv) curve	Test 3 ✅
5. Fetch QQQ option chain (expiries, strikes, IV)	yfinance — no IBKR	❌ not covered
6. Plot bucket rows on an Axes	tenor vs atmIv	❌ not covered
7. Wire into visualize_percentage_change	add 5th panel / 2×3 layout	❌ not covered
