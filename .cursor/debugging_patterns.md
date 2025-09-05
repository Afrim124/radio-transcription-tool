# Audio Processing Debugging Patterns

## Strategic Debug Print Placement

### **Workflow Flow Tracing**
```python
# BEFORE each major operation
print(f"DEBUG: Starting {operation_name}")
print(f"DEBUG: Input data: {len(input_data)} items")

# AFTER each major operation  
print(f"DEBUG: Completed {operation_name} in {time_taken:.1f} seconds")
print(f"DEBUG: Output data: {len(output_data)} items")
```

### **Critical Checkpoints**
```python
# At the start of each major function
print(f"DEBUG: Entering {function_name}")

# Before any external API calls
print(f"DEBUG: About to call {api_name}")

# After any external API calls
print(f"DEBUG: {api_name} returned successfully")

# Before any file operations
print(f"DEBUG: About to write to {filename}")

# After any file operations
print(f"DEBUG: Successfully wrote to {filename}")
```

## Audio Processing Specific Patterns

### **Chunk Processing Flow**
```python
for i, chunk in enumerate(audio_chunks):
    print(f"DEBUG: Processing chunk {i+1}/{len(audio_chunks)}")
    
    # Process chunk
    result = process_chunk(chunk)
    
    print(f"DEBUG: Chunk {i+1} completed, result: {len(result)} items")
    
    # Check for hanging
    if time.time() - chunk_start > max_chunk_time:
        print(f"DEBUG: Chunk {i+1} taking too long, forcing continue")
        continue
```

### **API Call Monitoring**
```python
# Before API call
api_start = time.time()
print(f"DEBUG: Calling {api_name}...")

# After API call
api_time = time.time() - api_start
print(f"DEBUG: {api_name} completed in {api_time:.1f} seconds")

# If API call takes too long
if api_time > expected_time:
    print(f"DEBUG: {api_name} took longer than expected")
```

## Hanging Detection Strategies

### **Progress Indicators**
```python
# Add progress prints in long loops
for i, item in enumerate(items):
    if i % 100 == 0:  # Every 100 items
        print(f"DEBUG: Processed {i}/{len(items)} items")
    
    # Process item
    process_item(item)
```

### **Time-based Checkpoints**
```python
# Set reasonable timeouts for each operation
max_operation_time = 300  # 5 minutes

# Check timeout at regular intervals
if time.time() - operation_start > max_operation_time:
    print(f"DEBUG: Operation taking too long, forcing completion")
    break  # or return, or raise exception
```

### **Resource Monitoring**
```python
# Monitor memory usage
import psutil
process = psutil.Process()
memory_usage = process.memory_info().rss / 1024 / 1024  # MB
print(f"DEBUG: Memory usage: {memory_usage:.1f} MB")

# Monitor CPU usage
cpu_percent = process.cpu_percent()
print(f"DEBUG: CPU usage: {cpu_percent}%")
```

## Common Hanging Points in Audio Processing

### **1. File I/O Operations**
- **Problem**: Writing large files, especially with complex formatting
- **Solution**: Add progress indicators and timeouts
- **Debug**: Print before/after each file operation

### **2. External API Calls**
- **Problem**: Network timeouts, API rate limits, authentication issues
- **Solution**: Implement retry logic with exponential backoff
- **Debug**: Monitor API response times and success rates

### **3. Memory-Intensive Operations**
- **Problem**: Processing large audio files, complex algorithms
- **Solution**: Process in chunks, monitor memory usage
- **Debug**: Track memory usage throughout the process

### **4. Threading Issues**
- **Problem**: Deadlocks, thread starvation, resource contention
- **Solution**: Use timeouts, avoid complex thread interactions
- **Debug**: Monitor thread states and completion times

## Emergency Recovery Patterns

### **Graceful Degradation**
```python
try:
    # Try the optimal approach
    result = optimal_processing(data)
except Exception as e:
    print(f"DEBUG: Optimal processing failed: {e}")
    # Fall back to simpler approach
    result = simple_processing(data)
```

### **Forced Completion**
```python
# If processing takes too long, force completion
if time.time() - start_time > max_total_time:
    print("DEBUG: Total time exceeded, forcing completion")
    # Generate minimal results
    result = generate_minimal_results()
    return result
```

### **State Preservation**
```python
# Save intermediate results periodically
if i % save_interval == 0:
    save_intermediate_results(results_so_far)
    print(f"DEBUG: Saved intermediate results at step {i}")
```

## Debug Output Best Practices

### **Structured Logging**
```python
# Use consistent format
print(f"DEBUG: [{operation}] {message}")

# Include relevant data
print(f"DEBUG: [KeyBERT] Extracted {len(keywords)} keywords from {len(text)} characters")

# Show progress
print(f"DEBUG: [Progress] {current}/{total} ({percentage:.1f}%)")
```

### **Error Context**
```python
try:
    result = risky_operation()
except Exception as e:
    print(f"DEBUG: [Error] {operation} failed: {e}")
    print(f"DEBUG: [Context] Input size: {len(input_data)}, Step: {current_step}")
```

## Key Debugging Rules

1. **Never assume the problem is where the last debug print suggests**
2. **Add debug prints BEFORE and AFTER each operation, not just during**
3. **Use time-based checkpoints to identify hanging operations**
4. **Monitor resources (memory, CPU) throughout the process**
5. **Implement graceful fallbacks for critical operations**
6. **Save intermediate results to prevent complete data loss**
7. **Test each change incrementally before proceeding**
8. **When in doubt, revert to working code and start over**
