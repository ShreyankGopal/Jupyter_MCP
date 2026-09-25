"""
CellExecutor for executing code on Jupyter kernels and capturing output messages.
"""

import queue
import time
from typing import Dict, Any, List, Optional


class CellExecutor:
    """Handles execution of code against a Jupyter kernel and collects output streams."""

    def __init__(self, default_timeout: int = 30):
        self.default_timeout = default_timeout

    def execute(self, kernel_client: Any, code: str, timeout: Optional[int] = None) -> Dict[str, Any]:
        """
        Execute code string via the kernel client and collect all outputs.

        Args:
            kernel_client: The active jupyter_client KernelClient instance.
            code: Source code string to execute.
            timeout: Maximum seconds to wait for execution to complete.

        Returns:
            Dictionary containing:
            {
                'status': 'ok' | 'error' | 'timeout',
                'execution_count': Optional[int],
                'outputs': List[dict],  # nbformat compatible outputs
                'ename': Optional[str],
                'evalue': Optional[str],
                'traceback': Optional[List[str]]
            }
        """
        if kernel_client is None:
            raise RuntimeError("Kernel client is not initialized or running")

        exec_timeout = timeout if timeout is not None else self.default_timeout
        
        # Send execute request over shell channel
        msg_id = kernel_client.execute(code)
        # send execute request over shell channel, but collect output sream from IO pub sub. here we subscribe to all topics
        outputs: List[Dict[str, Any]] = []
        execution_count: Optional[int] = None
        status = "ok"
        ename: Optional[str] = None
        evalue: Optional[str] = None
        traceback: Optional[List[str]] = None
        # initialising the output format
        start_time = time.time()

        try:
            # Collect IOPub messages until idle status for this msg_id is received
            while True:
                elapsed = time.time() - start_time ## if the elapsed time> timeout we break and make status as timeout
                remaining_time = max(0.1, exec_timeout - elapsed)
                if elapsed > exec_timeout:
                    status = "timeout"
                    break

                try:
                    msg = kernel_client.get_iopub_msg(timeout=remaining_time)
                except queue.Empty:
                    if (time.time() - start_time) > exec_timeout:
                        status = "timeout"
                        break
                    continue

                # Filter messages related to this execution request
                parent_msg_id = msg.get("parent_header", {}).get("msg_id")
                if parent_msg_id and parent_msg_id != msg_id:
                    continue

                msg_type = msg.get("header", {}).get("msg_type")
                content = msg.get("content", {})

                if msg_type == "status":
                    if content.get("execution_state") == "idle" and parent_msg_id == msg_id:
                        # Execution is complete
                        break

                elif msg_type == "execute_input":
                    if "execution_count" in content:
                        execution_count = content["execution_count"]

                elif msg_type == "stream":
                    stream_name = content.get("name", "stdout")
                    stream_text = content.get("text", "")
                    
                    # Merge sequential stream outputs of the same stream name if applicable
                    if outputs and outputs[-1].get("output_type") == "stream" and outputs[-1].get("name") == stream_name:
                        outputs[-1]["text"] += stream_text
                    else:
                        outputs.append({
                            "output_type": "stream",
                            "name": stream_name,
                            "text": stream_text
                        })

                elif msg_type == "execute_result":
                    execution_count = content.get("execution_count", execution_count)
                    outputs.append({
                        "output_type": "execute_result",
                        "data": content.get("data", {}),
                        "metadata": content.get("metadata", {}),
                        "execution_count": execution_count
                    })

                elif msg_type == "display_data":
                    outputs.append({
                        "output_type": "display_data",
                        "data": content.get("data", {}),
                        "metadata": content.get("metadata", {})
                    })

                elif msg_type == "error":
                    status = "error"
                    ename = content.get("ename")
                    evalue = content.get("evalue")
                    traceback = content.get("traceback", [])
                    outputs.append({
                        "output_type": "error",
                        "ename": ename,
                        "evalue": evalue,
                        "traceback": traceback
                    })

                elif msg_type == "clear_output":
                    outputs = []

            # Retrieve reply from shell channel if not timed out
            if status != "timeout":
                try:
                    remaining_shell_time = max(0.5, exec_timeout - (time.time() - start_time))
                    reply = kernel_client.get_shell_msg(timeout=remaining_shell_time)
                    reply_content = reply.get("content", {})
                    if "execution_count" in reply_content and reply_content["execution_count"] is not None:
                        execution_count = reply_content["execution_count"]
                    if reply_content.get("status") == "error":
                        status = "error"
                        ename = reply_content.get("ename", ename)
                        evalue = reply_content.get("evalue", evalue)
                        traceback = reply_content.get("traceback", traceback)
                except queue.Empty:
                    pass

        except Exception as e:
            status = "error"
            evalue = str(e)
            ename = type(e).__name__

        return {
            "status": status,
            "execution_count": execution_count,
            "outputs": outputs,
            "ename": ename,
            "evalue": evalue,
            "traceback": traceback
        }
