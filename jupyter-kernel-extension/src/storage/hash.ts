/**
 * SHA256 hash implementation for kernel ID generation
 * Replicates Python's calculate_kernel_id() functionality
 */

import * as crypto from 'crypto';
import * as path from 'path';

/**
 * Calculate a SHA256 hash-based kernel ID from the notebook's absolute path.
 * This matches the Python implementation for cross-tool compatibility.
 * 
 * @param notebookPath - Path to the notebook file
 * @returns SHA256 hash of the absolute path as a hexadecimal string
 */
export function calculateKernelId(notebookPath: string): string {
  // Resolve to absolute path (matches Python's Path.resolve())
  const absolutePath = path.resolve(notebookPath);
  
  // Generate SHA256 hash (matches Python's hashlib.sha256())
  const hash = crypto.createHash('sha256');
  hash.update(absolutePath);
  
  // Return hexadecimal string (matches Python's hexdigest())
  return hash.digest('hex');
}

/**
 * Verify that two paths have the same kernel ID (same hash)
 * Useful for testing cross-platform consistency
 * 
 * @param path1 - First path to compare
 * @param path2 - Second path to compare
 * @returns true if both paths generate the same kernel ID
 */
export function kernelIdsMatch(path1: string, path2: string): boolean {
  return calculateKernelId(path1) === calculateKernelId(path2);
}
