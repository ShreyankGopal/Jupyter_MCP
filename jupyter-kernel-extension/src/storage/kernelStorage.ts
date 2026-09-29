/**
 * JSON storage operations for kernel information
 * Replicates Python's kernel storage functionality for cross-tool compatibility
 */

import * as fs from 'fs/promises';
import * as path from 'path';
import * as os from 'os';
import { KernelInfo } from './types';

// Global lock simulation for file operations (prevents in-process race conditions)
const fileLocks = new Map<string, Promise<void>>();

/**
 * Get the cross-platform kernel storage directory.
 * Matches Python's get_kernel_storage_dir() functionality.
 * 
 * @returns Path object for the kernel storage directory (~/.jupyter-mcp-kernel/)
 */
export function getKernelStorageDir(): string {
  const kernelDir = path.join(os.homedir(), '.jupyter-mcp-kernel');
  
  // Ensure directory exists (matches Python's mkdir(exist_ok=True))
  fs.mkdir(kernelDir, { recursive: true }).catch((err: NodeJS.ErrnoException) => {
    if (err.code !== 'EEXIST') {
      throw err;
    }
  });
  
  return kernelDir;
}

/**
 * Save kernel information to a JSON file.
 * Replicates Python's save_kernel_info() functionality.
 * 
 * @param kernelId - The SHA256-based kernel ID
 * @param kernelInfo - Dictionary containing kernel information
 */
export async function saveKernelInfo(kernelId: string, kernelInfo: Partial<KernelInfo>): Promise<void> {
  const kernelDir = getKernelStorageDir();
  const kernelFile = path.join(kernelDir, `${kernelId}.json`);
  
  // Add timestamp if not present (matches Python logic)
  const now = new Date().toISOString();
  const kernelInfoWithTimestamps = {
    ...kernelInfo,
    last_updated: kernelInfo.last_updated || now,
    created_at: kernelInfo.created_at || now
  };
  
  // Simple file locking simulation
  if (fileLocks.has(kernelFile)) {
    await fileLocks.get(kernelFile);
  }
  
  const lockPromise = (async () => {
    try {
      await fs.writeFile(kernelFile, JSON.stringify(kernelInfoWithTimestamps, null, 2));
    } finally {
      fileLocks.delete(kernelFile);
    }
  })();
  
  fileLocks.set(kernelFile, lockPromise);
  await lockPromise;
}

/**
 * Load kernel information from a JSON file.
 * Replicates Python's load_kernel_info() functionality.
 * 
 * @param kernelId - The SHA256-based kernel ID
 * @returns Dictionary containing kernel information, or null if file doesn't exist
 */
export async function loadKernelInfo(kernelId: string): Promise<KernelInfo | null> {
  const kernelDir = getKernelStorageDir();
  const kernelFile = path.join(kernelDir, `${kernelId}.json`);
  
  try {
    await fs.access(kernelFile);
  } catch {
    return null; // File doesn't exist
  }
  
  try {
    const data = await fs.readFile(kernelFile, 'utf-8');
    return JSON.parse(data) as KernelInfo;
  } catch (error: unknown) {
    // Handle corrupted JSON files (matches Python error handling)
    console.warn(`Warning: Could not load kernel info for ${kernelId}: ${error}`);
    return null;
  }
}

/**
 * Delete kernel information JSON file.
 * Replicates Python's delete_kernel_info() functionality.
 * 
 * @param kernelId - The SHA256-based kernel ID
 * @returns true if file was deleted, false if it didn't exist
 */
export async function deleteKernelInfo(kernelId: string): Promise<boolean> {
  const kernelDir = getKernelStorageDir();
  const kernelFile = path.join(kernelDir, `${kernelId}.json`);
  
  try {
    await fs.unlink(kernelFile);
    return true;
  } catch (error: unknown) {
    if (error instanceof Error && (error as NodeJS.ErrnoException).code === 'ENOENT') {
      return false; // File doesn't exist
    }
    throw error;
  }
}

/**
 * Clean up kernel files that are older than specified days.
 * Replicates Python's cleanup_stale_kernels() functionality.
 * 
 * @param maxAgeDays - Maximum age in days before cleanup
 * @returns Number of files cleaned up
 */
export async function cleanupStaleKernels(maxAgeDays: number = 2): Promise<number> {
  const kernelDir = getKernelStorageDir();
  let cleanedCount = 0;
  
  const cutoffTime = Date.now() - (maxAgeDays * 24 * 3600 * 1000);
  
  try {
    const files = await fs.readdir(kernelDir);
    
    for (const file of files) {
      if (file.endsWith('.json')) {
        const filePath = path.join(kernelDir, file);
        
        try {
          const stats = await fs.stat(filePath);
          if (stats.mtimeMs < cutoffTime) {
            await fs.unlink(filePath);
            cleanedCount++;
          }
        } catch (error) {
          console.warn(`Warning: Could not clean up ${filePath}: ${error}`);
        }
      }
    }
  } catch (error) {
    console.warn(`Warning: Could not read kernel directory: ${error}`);
  }
  
  return cleanedCount;
}