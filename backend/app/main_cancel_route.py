# Cancel route to be added to main.py

@app.post("/api/v1/runs/{run_id}/cancel")
async def cancel_run(run_id: str):
    """
    Cancel a running video generation task.
    Revokes all pending/running Celery tasks and marks FSM as FAILED.
    """
    from app.api.cancel import cancel_run_handler
    return await cancel_run_handler(run_id, runs)
