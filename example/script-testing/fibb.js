// fibonacci.js

/**
 * Calculates the nth Fibonacci number using recursion.
 *
 * @param {number} n The index of the Fibonacci number to calculate (starting from 0).
 * @returns {number} The nth Fibonacci number.  Returns NaN if n is negative.
 */
function fibonacciRecursive(n) {
  if (n < 0) {
    return NaN; // Handle negative input
  }
  if (n <= 1) {
    return n;
  }
  return fibonacciRecursive(n - 1) + fibonacciRecursive(n - 2);
}


/**
 * Calculates the nth Fibonacci number using iteration (dynamic programming).
 * This is generally more efficient than the recursive approach for larger values of n.
 *
 * @param {number} n The index of the Fibonacci number to calculate (starting from 0).
 * @returns {number} The nth Fibonacci number. Returns NaN if n is negative.
 */
function fibonacciIterative(n) {
  if (n < 0) {
    return NaN; // Handle negative input
  }
  if (n <= 1) {
    return n;
  }

  let a = 0;
  let b = 1;
  for (let i = 2; i <= n; i++) {
    const temp = a + b;
    a = b;
    b = temp;
  }
  return b;
}


// Example usage (using recursive approach)
const n = 10; // Calculate the 10th Fibonacci number
const resultRecursive = fibonacciRecursive(n);
console.log(`Fibonacci(${n}) (recursive): ${resultRecursive}`);

// Example usage (using iterative approach)
const resultIterative = fibonacciIterative(n);
console.log(`Fibonacci(${n}) (iterative): ${resultIterative}`);


// You can also add a command-line argument to specify the number
// and run the script like this: node fibonacci.js 15
if (process.argv.length > 2) {
  const num = parseInt(process.argv[2]);
  if (!isNaN(num)) {
    console.log(`Fibonacci(${num}) (iterative): ${fibonacciIterative(num)}`);
  } else {
    console.error("Invalid input. Please provide a number as a command-line argument.");
  }
}
