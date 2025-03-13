"""
Benchmarking and performance tuning for the MCP eRegulations server.
"""
import time
import asyncio
import statistics
import logging
from typing import Dict, Any, List, Callable, Tuple
import matplotlib.pyplot as plt
import numpy as np

from mcp_eregulations.api.client import ERegulationsClient
from mcp_eregulations.api.detailed_client import detailed_client
from mcp_eregulations.utils.indexing import index
from mcp_eregulations.utils.query_handling import query_handler
from mcp_eregulations.utils.optimization import cache

logger = logging.getLogger(__name__)

class Benchmark:
    """Class for benchmarking and performance tuning."""
    
    def __init__(self):
        """Initialize the benchmark."""
        self.results = {}
    
    async def benchmark_function(
        self, 
        func: Callable, 
        args: List = None, 
        kwargs: Dict = None, 
        iterations: int = 10,
        name: str = None
    ) -> Dict[str, Any]:
        """
        Benchmark a function.
        
        Args:
            func: The function to benchmark
            args: List of positional arguments
            kwargs: Dictionary of keyword arguments
            iterations: Number of iterations to run
            name: Name for the benchmark
            
        Returns:
            Dictionary with benchmark results
        """
        args = args or []
        kwargs = kwargs or {}
        name = name or func.__name__
        
        logger.info(f"Benchmarking {name} for {iterations} iterations")
        
        execution_times = []
        
        for i in range(iterations):
            start_time = time.time()
            await func(*args, **kwargs)
            execution_time = time.time() - start_time
            execution_times.append(execution_time)
            
            logger.debug(f"Iteration {i+1}/{iterations}: {execution_time:.4f} seconds")
            
            # Small delay between iterations
            await asyncio.sleep(0.1)
        
        # Calculate statistics
        avg_time = statistics.mean(execution_times)
        min_time = min(execution_times)
        max_time = max(execution_times)
        median_time = statistics.median(execution_times)
        stdev = statistics.stdev(execution_times) if len(execution_times) > 1 else 0
        
        result = {
            "name": name,
            "iterations": iterations,
            "avg_time": avg_time,
            "min_time": min_time,
            "max_time": max_time,
            "median_time": median_time,
            "stdev": stdev,
            "raw_times": execution_times
        }
        
        self.results[name] = result
        
        logger.info(f"Benchmark results for {name}:")
        logger.info(f"  Average: {avg_time:.4f} seconds")
        logger.info(f"  Min: {min_time:.4f} seconds")
        logger.info(f"  Max: {max_time:.4f} seconds")
        logger.info(f"  Median: {median_time:.4f} seconds")
        logger.info(f"  StdDev: {stdev:.4f} seconds")
        
        return result
    
    async def benchmark_with_and_without_cache(
        self, 
        func: Callable, 
        args: List = None, 
        kwargs: Dict = None, 
        iterations: int = 10,
        name: str = None
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Benchmark a function with and without caching.
        
        Args:
            func: The function to benchmark
            args: List of positional arguments
            kwargs: Dictionary of keyword arguments
            iterations: Number of iterations to run
            name: Name for the benchmark
            
        Returns:
            Tuple of benchmark results (without_cache, with_cache)
        """
        args = args or []
        kwargs = kwargs or {}
        name = name or func.__name__
        
        # Clear the cache
        cache.clear()
        
        # Benchmark without cache (first call)
        logger.info(f"Benchmarking {name} without cache")
        without_cache = await self.benchmark_function(
            func, args, kwargs, 1, f"{name}_without_cache"
        )
        
        # Benchmark with cache
        logger.info(f"Benchmarking {name} with cache")
        with_cache = await self.benchmark_function(
            func, args, kwargs, iterations, f"{name}_with_cache"
        )
        
        # Calculate improvement
        improvement = without_cache["avg_time"] / with_cache["avg_time"]
        logger.info(f"Cache improvement: {improvement:.2f}x faster")
        
        return without_cache, with_cache
    
    async def benchmark_api_client(self, iterations: int = 5) -> None:
        """
        Benchmark the API client.
        
        Args:
            iterations: Number of iterations to run
        """
        client = ERegulationsClient()
        
        # Benchmark get_procedure
        await self.benchmark_function(
            client.get_procedure,
            [1],  # procedure_id
            {},
            iterations,
            "api_client_get_procedure"
        )
        
        # Benchmark get_procedure_steps
        await self.benchmark_function(
            client.get_procedure_steps,
            [1],  # procedure_id
            {},
            iterations,
            "api_client_get_procedure_steps"
        )
        
        # Benchmark get_procedure_requirements
        await self.benchmark_function(
            client.get_procedure_requirements,
            [1],  # procedure_id
            {},
            iterations,
            "api_client_get_procedure_requirements"
        )
    
    async def benchmark_detailed_client(self, iterations: int = 5) -> None:
        """
        Benchmark the detailed client.
        
        Args:
            iterations: Number of iterations to run
        """
        # Benchmark get_procedure_detailed
        await self.benchmark_function(
            detailed_client.get_procedure_detailed,
            [1],  # procedure_id
            {},
            iterations,
            "detailed_client_get_procedure_detailed"
        )
        
        # Benchmark get_institution_info
        await self.benchmark_function(
            detailed_client.get_institution_info,
            [1],  # institution_id
            {},
            iterations,
            "detailed_client_get_institution_info"
        )
    
    async def benchmark_indexing(self, iterations: int = 5) -> None:
        """
        Benchmark the indexing functionality.
        
        Args:
            iterations: Number of iterations to run
        """
        # Prepare test data
        procedure_data = {
            "id": 999,
            "title": "Test Procedure",
            "description": "Test Description",
            "additionalInfo": "Additional Info",
            "blocks": [
                {
                    "steps": [
                        {
                            "id": 1,
                            "title": "Step 1",
                            "description": "Step 1 Description"
                        },
                        {
                            "id": 2,
                            "title": "Step 2",
                            "description": "Step 2 Description"
                        }
                    ]
                }
            ]
        }
        
        # Benchmark index_procedure
        await self.benchmark_function(
            lambda: index.index_procedure(999, procedure_data),
            [],
            {},
            iterations,
            "indexing_index_procedure"
        )
        
        # Benchmark search_procedures
        await self.benchmark_function(
            lambda: index.search_procedures("test"),
            [],
            {},
            iterations,
            "indexing_search_procedures"
        )
        
        # Benchmark get_procedure
        await self.benchmark_function(
            lambda: index.get_procedure(999),
            [],
            {},
            iterations,
            "indexing_get_procedure"
        )
    
    async def benchmark_query_handling(self, iterations: int = 5) -> None:
        """
        Benchmark the query handling functionality.
        
        Args:
            iterations: Number of iterations to run
        """
        # Benchmark process_query
        await self.benchmark_function(
            query_handler.process_query,
            ["What is procedure 1 about?"],
            {},
            iterations,
            "query_handling_process_query"
        )
        
        # Benchmark generate_response
        query_result = await query_handler.process_query("What is procedure 1 about?")
        await self.benchmark_function(
            query_handler.generate_response,
            [query_result],
            {},
            iterations,
            "query_handling_generate_response"
        )
    
    async def benchmark_with_cache(self, iterations: int = 5) -> None:
        """
        Benchmark functions with caching.
        
        Args:
            iterations: Number of iterations to run
        """
        # Benchmark get_procedure with and without cache
        await self.benchmark_with_and_without_cache(
            detailed_client.get_procedure,
            [1],  # procedure_id
            {},
            iterations,
            "get_procedure_cache_comparison"
        )
        
        # Benchmark get_procedure_detailed with and without cache
        await self.benchmark_with_and_without_cache(
            detailed_client.get_procedure_detailed,
            [1],  # procedure_id
            {},
            iterations,
            "get_procedure_detailed_cache_comparison"
        )
    
    def generate_report(self, output_file: str = "/home/ubuntu/mcp-eregulations/benchmark_report.md") -> None:
        """
        Generate a benchmark report.
        
        Args:
            output_file: Path to the output file
        """
        report = "# MCP eRegulations Server Benchmark Report\n\n"
        report += f"Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        # Group results by category
        categories = {
            "API Client": [r for r in self.results.values() if r["name"].startswith("api_client_")],
            "Detailed Client": [r for r in self.results.values() if r["name"].startswith("detailed_client_")],
            "Indexing": [r for r in self.results.values() if r["name"].startswith("indexing_")],
            "Query Handling": [r for r in self.results.values() if r["name"].startswith("query_handling_")],
            "Cache Comparison": [r for r in self.results.values() if r["name"].endswith("_cache_comparison") or 
                                r["name"].endswith("_with_cache") or 
                                r["name"].endswith("_without_cache")]
        }
        
        # Add results by category
        for category, results in categories.items():
            if results:
                report += f"## {category}\n\n"
                report += "| Function | Iterations | Avg Time (s) | Min Time (s) | Max Time (s) | Median Time (s) | StdDev (s) |\n"
                report += "|----------|------------|--------------|--------------|--------------|-----------------|------------|\n"
                
                for result in sorted(results, key=lambda x: x["name"]):
                    report += f"| {result['name']} | {result['iterations']} | {result['avg_time']:.4f} | {result['min_time']:.4f} | {result['max_time']:.4f} | {result['median_time']:.4f} | {result['stdev']:.4f} |\n"
                
                report += "\n"
        
        # Add cache comparison section if available
        cache_pairs = []
        for name in self.results:
            if name.endswith("_without_cache"):
                with_cache_name = name.replace("_without_cache", "_with_cache")
                if with_cache_name in self.results:
                    cache_pairs.append((name, with_cache_name))
        
        if cache_pairs:
            report += "## Cache Performance Improvement\n\n"
            report += "| Function | Without Cache (s) | With Cache (s) | Improvement Factor |\n"
            report += "|----------|------------------|----------------|--------------------|\n"
            
            for without_cache_name, with_cache_name in cache_pairs:
                without_cache = self.results[without_cache_name]
                with_cache = self.results[with_cache_name]
                improvement = without_cache["avg_time"] / with_cache["avg_time"] if with_cache["avg_time"] > 0 else float('inf')
                
                base_name = without_cache_name.replace("_without_cache", "")
                report += f"| {base_name} | {without_cache['avg_time']:.4f} | {with_cache['avg_time']:.4f} | {improvement:.2f}x |\n"
            
            report += "\n"
        
        # Write the report to file
        with open(output_file, "w") as f:
            f.write(report)
        
        logger.info(f"Benchmark report generated: {output_file}")
    
    def generate_charts(self, output_dir: str = "/home/ubuntu/mcp-eregulations/benchmark_charts") -> None:
        """
        Generate benchmark charts.
        
        Args:
            output_dir: Directory for the output charts
        """
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate bar chart for average execution times
        plt.figure(figsize=(12, 8))
        
        names = []
        avg_times = []
        
        for name, result in sorted(self.results.items(), key=lambda x: x[1]["avg_time"]):
            if not name.endswith("_cache_comparison"):
                names.append(name)
                avg_times.append(result["avg_time"])
        
        plt.barh(names, avg_times)
        plt.xlabel("Average Execution Time (seconds)")
        plt.title("Average Execution Time by Function")
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, "avg_execution_times.png"))
        plt.close()
        
        # Generate cache comparison chart if available
        cache_pairs = []
        for name in self.results:
            if name.endswith("_without_cache"):
                with_cache_name = name.replace("_without_cache", "_with_cache")
                if with_cache_name in self.results:
                    cache_pairs.append((name, with_cache_name))
        
        if cache_pairs:
            plt.figure(figsize=(10, 6))
            
            labels = []
            without_cache_times = []
            with_cache_times = []
            
            for without_cache_name, with_cache_name in cache_pairs:
                base_name = without_cache_name.replace("_without_cache", "")
                labels.append(base_name)
                without_cache_times.append(self.results[without_cache_name]["avg_time"])
                with_cache_times.append(self.results[with_cache_name]["avg_time"])
            
            x = np.arange(len(labels))
            width = 0.35
            
            fig, ax = plt.subplots(figsize=(12, 8))
            rects1 = ax.bar(x - width/2, without_cache_times, width, label="Without Cache")
            rects2 = ax.bar(x + width/2, with_cache_times, width, label="With Cache")
            
            ax.set_ylabel("Execution Time (seconds)")
            ax.set_title("Cache Performance Comparison")
            ax.set_xticks(x)
            ax.set_xticklabels(labels)
            ax.legend()
            
            fig.tight_layout()
            plt.savefig(os.path.join(output_dir, "cache_comparison.png"))
            plt.close()
        
        logger.info(f"Benchmark charts generated in: {output_dir}")


async def run_benchmarks():
    """Run benchmarks for the MCP eRegulations server."""
    benchmark = Benchmark()
    
    # Run benchmarks
    await benchmark.benchmark_api_client()
    await benchmark.benchmark_detailed_client()
    await benchmark.benchmark_indexing()
    await benchmark.benchmark_query_handling()
    await benchmark.benchmark_with_cache()
    
    # Generate report and charts
    benchmark.generate_report()
    benchmark.generate_charts()
    
    return benchmark


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_benchmarks())
