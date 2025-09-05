# Radio Transcription Tool - Lessons Learned

## Critical Debugging Principles

### 1. **Verify the Actual Problem First**
- **NEVER assume the problem is what the debug output suggests**
- **ALWAYS trace the execution flow step-by-step before making changes**
- **Debug output can be misleading - the hang might be happening AFTER the last debug print**

### 2. **The "Last Debug Print" Trap**
- If the last debug output shows "Process finished with exit code 0", the program isn't hanging
- If the last debug output shows normal completion but the program appears frozen, the hang is happening AFTER that point
- **Key insight**: The hang location is AFTER the last successful debug print, not during the operation that produced it

### 3. **Avoid Premature Optimization**
- **Don't fix what isn't broken**
- If a working version exists (v3.2), use it as the foundation
- **Never rewrite working code** - make minimal, targeted fixes only
- **"If it ain't broke, don't fix it"** applies especially to complex audio processing workflows

### 4. **Timeout Protection Strategy**
- **Don't add timeouts everywhere** - identify the specific hanging point first
- **Timeouts can mask the real problem** instead of solving it
- **Aggressive timeouts can break working functionality**
- **Focus on the root cause, not symptoms**

### 5. **Code Flow Analysis**
- **Map the execution path** before making changes
- **Identify where the program actually stops** vs. where you think it stops
- **Use strategic debug prints** to trace flow, not just to show results
- **The hang is usually in the "quiet" sections** between debug prints

## What Went Wrong in This Case

### **Initial Misdiagnosis**
- Debug showed "KeyBERT extraction timed out" → Assumed KeyBERT was the problem
- **Reality**: KeyBERT was working fine, the hang was happening later

### **Over-Engineering the Solution**
- Added multiple timeout layers without understanding the real issue
- Implemented complex fallback strategies that weren't needed
- **Result**: Made the code more complex and introduced new bugs

### **Ignoring Working Code**
- Had a working v3.2 version but tried to "fix" it
- **Lesson**: Working code is precious - don't break it

## Best Practices Going Forward

### **Before Making Any Changes**
1. **Confirm the actual problem location** with strategic debug prints
2. **Verify the working baseline** (v3.2 in this case)
3. **Make minimal, targeted changes** only where needed
4. **Test each change incrementally**

### **Debug Strategy**
1. **Add debug prints BEFORE and AFTER each major operation**
2. **Don't just show results - show progress through the workflow**
3. **Identify the exact line where execution stops**
4. **Use the debug output to trace flow, not just diagnose problems**

### **When Things Go Wrong**
1. **Revert to the last working version immediately**
2. **Don't try to fix broken code - start fresh from working code**
3. **Document what you tried and why it failed**
4. **Learn from the failure before attempting another fix**

## Key Takeaway

**The most dangerous debugging mistake is solving the wrong problem.** Always verify the actual issue before implementing any solution, and never break working code in an attempt to "improve" it.
