import argparse
import time
import json
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
import os

def send_request(url, file_path):
    start_time = time.time()
    if not os.path.exists(file_path):
        return {"success": False, "error": f"File {file_path} not found", "latency": 0.0}
        
    try:
        # Construct multipart/form-data payload manually to keep script dependency-free
        boundary = '----BenchmarkBoundary' + str(time.time())
        parts = []
        with open(file_path, 'rb') as f:
            file_content = f.read()
            
        parts.append(f'--{boundary}')
        parts.append(f'Content-Disposition: form-data; name="file"; filename="{os.path.basename(file_path)}"')
        
        # Detect basic content type from extension
        ext = os.path.splitext(file_path)[1].lower()
        content_type = "audio/wav"
        if ext == ".mp3":
            content_type = "audio/mp3"
        elif ext == ".m4a":
            content_type = "audio/m4a"
        elif ext == ".aac":
            content_type = "audio/aac"
            
        parts.append(f'Content-Type: {content_type}')
        parts.append('')
        parts.append(file_content)
        parts.append(f'--{boundary}--')
        parts.append('')
        
        # Combine parts into binary payload
        body = b''
        for p in parts:
            if isinstance(p, bytes):
                body += p + b'\r\n'
            else:
                body += p.encode('utf-8') + b'\r\n'
                
        headers = {
            'Content-Type': f'multipart/form-data; boundary={boundary}',
            'Content-Length': str(len(body))
        }
        
        req = urllib.request.Request(f"{url}/transcribe", data=body, headers=headers, method='POST')
        with urllib.request.urlopen(req, timeout=120) as response:
            res_body = response.read().decode('utf-8')
            res_data = json.loads(res_body)
            success = res_data.get("success", False)
            latency = time.time() - start_time
            return {"success": success, "latency": latency, "error": None}
            
    except urllib.error.HTTPError as e:
        try:
            err_body = e.read().decode('utf-8')
            err_data = json.loads(err_body)
            err_msg = err_data.get("error", f"HTTP Error {e.code}")
        except Exception:
            err_msg = f"HTTP Error {e.code}"
        return {"success": False, "latency": time.time() - start_time, "error": err_msg}
    except Exception as e:
        return {"success": False, "latency": time.time() - start_time, "error": str(e)}

def run_suite(url, file_path, num_requests, concurrency):
    print(f"\n--- Running Benchmark Suite: {num_requests} total requests (Concurrency: {concurrency}) ---")
    results = []
    
    start_suite = time.time()
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(send_request, url, file_path) for _ in range(num_requests)]
        
        for future in as_completed(futures):
            res = future.result()
            results.append(res)
            
    total_suite_time = time.time() - start_suite
    
    successes = [r for r in results if r["success"]]
    failures = [r for r in results if not r["success"]]
    success_rate = (len(successes) / num_requests) * 100
    
    latencies = [r["latency"] for r in successes]
    avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
    max_latency = max(latencies) if latencies else 0.0
    min_latency = min(latencies) if latencies else 0.0
    
    print(f"Completed suite in: {total_suite_time:.2f} seconds")
    print(f"Success Rate:      {success_rate:.1f}% ({len(successes)}/{num_requests})")
    if successes:
        print(f"Average Latency:   {avg_latency:.2f} seconds")
        print(f"Minimum Latency:   {min_latency:.2f} seconds")
        print(f"Maximum Latency:   {max_latency:.2f} seconds")
    if failures:
        print(f"Failures count:    {len(failures)}")
        print(f"Sample failure:    {failures[0]['error']}")
        
    return {
        "num_requests": num_requests,
        "success_rate": success_rate,
        "avg_latency": avg_latency,
        "max_latency": max_latency,
        "total_time": total_suite_time
    }

def main():
    parser = argparse.ArgumentParser(description="Load Testing / Benchmarking Tool for Hindi-ASR GPU API")
    parser.add_argument("--url", default="http://127.0.0.1:8000", help="ASR API Backend base URL (default: http://127.0.0.1:8000)")
    parser.add_argument("--audio", required=True, help="Path to sample audio file for testing")
    parser.add_argument("--concurrency", type=int, default=5, help="Number of concurrent threads to use (default: 5)")
    args = parser.parse_args()
    
    print("====================================================")
    print("       HINDI-ASR LOAD TESTING BENCHMARK TOOL        ")
    print("====================================================")
    print(f"Target Server URL:   {args.url}")
    print(f"Test Audio File:     {args.audio}")
    print(f"Worker Concurrency:  {args.concurrency}")
    print("====================================================")
    
    # Run three sequential benchmark suites
    run_suite(args.url, args.audio, 10, args.concurrency)
    run_suite(args.url, args.audio, 25, args.concurrency)
    run_suite(args.url, args.audio, 50, args.concurrency)
    
if __name__ == "__main__":
    main()
