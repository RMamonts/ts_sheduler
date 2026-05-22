import subprocess
from pathlib import Path

import streamlit as st

st.set_page_config(page_title="Task Spooler", layout="wide")
st.title("🚀 Task Spooler - Command Queue")

# Sidebar for queue management
st.sidebar.header("Queue Management")


# Function to check if ts is available
def check_ts_installed():
    try:
        result = subprocess.run(["which", "tsp"], capture_output=True, text=True)
        return result.returncode == 0
    except Exception:
        return False


if not check_ts_installed():
    st.error("❌ Task spooler (ts) is not installed. Please install it first.")
    st.code("# Install ts (task spooler)")
    st.stop()


# Function to add command to queue
def add_to_queue(command):
    try:
        # Add command to ts queue using bash for proper shell syntax support
        result = subprocess.run(
            ["tsp", "bash", "-c", command],
            capture_output=True,
            text=True,
            timeout=600,
        )

        if result.returncode == 0:
            return True, "Command added to queue successfully"
        else:
            return False, f"tsp error: {result.stderr}"
    except subprocess.TimeoutExpired:
        return True, "Command added to queue (timeout reached during submission)"
    except Exception as e:
        return False, str(e)


# Function to get queue status
def get_queue_status():
    try:
        result = subprocess.run(
            ["tsp", "-l"], capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            header = "ID   State      Output               E-Level  Times(r/u/s)   Command [run=0/1]"
            res = result.stdout.replace(header, "")
            return res
        return ""
    except Exception:
        return ""


# Function to get job info from queue output
def parse_queue_status(queue_output):
    jobs = []
    if not queue_output.strip():
        return jobs

    lines = queue_output.strip().split("\n")
    for line in lines:
        # Parse ts -l output format
        # Example: "1      username command..."
        if line.strip():
            parts = line.split()
            if len(parts) >= 2:
                job_id = parts[0]
                # The command is everything after the job ID and user
                command = " ".join(parts[1:])
                jobs.append({"id": job_id, "command": command})
    return jobs


# Function to remove job from queue
def remove_job(job_id):
    try:
        result = subprocess.run(
            ["tsp", "-r", job_id], capture_output=True, text=True, timeout=5
        )
        return result.returncode == 0, f"Job {job_id} removed from queue"
    except Exception as e:
        return False, str(e)


# Function to get job output
def get_job_output(job_id):
    try:
        result = subprocess.run(
            ["bash", "-c", f'tail -n 10 "$(tsp -o {job_id})"'],
            capture_output=True, text=True, timeout=5
        )
        return result.stdout or "No output yet or job not finished"
    except Exception as e:
        return str(e)


# Function to clear all jobs
def clear_queue():
    try:
        result = subprocess.run(
            ["tsp", "-K"], capture_output=True, text=True, timeout=5
        )
        return result.returncode == 0, "Queue cleared"
    except Exception as e:
        return False, str(e)


# Refresh button
if st.sidebar.button("🔄 Refresh Queue"):
    st.rerun()

if st.sidebar.button("🗑️ Clear All Jobs"):
    success, msg = clear_queue()
    if success:
        st.sidebar.success(msg)
        st.rerun()
    else:
        st.sidebar.error(msg)

# Add command section
st.header("Add branch to test")
commit = st.text_input(
    "Branch name",
    placeholder="e.g., feature/my-awesome-branch",
    help="Branch name to test — will be added to the queue and executed sequentially",
)

col1, col2 = st.columns([1, 4])
with col1:
    add_btn = st.button("Add to Queue", type="primary", use_container_width=True)

if add_btn and commit.strip():
    venv_python = Path(__file__).resolve().parents[2] / ".venv" / "bin" / "python"
    main = Path(__file__).resolve()

    command = f"{venv_python} {main} --mamont-branch {commit}"

    success, msg = add_to_queue(command)
    if success:
        st.success(f"✅ {msg}")
    else:
        st.error(f"❌ Failed to add command: {msg}")

# Display queue status
st.header("📋 Queue Status")
queue_output = get_queue_status()

# Parse and display jobs
jobs = parse_queue_status(queue_output)

if jobs:
    st.write(f"**Total jobs in queue: {len(jobs)}**")

    for idx, job in enumerate(jobs):
        with st.expander(
            f"Job #{job['id']}: {job['command'][:60]}..."
            if len(job["command"]) > 60
            else f"Job #{job['id']}: {job['command']}"
        ):
            st.write(f"**Command:** `{job['command']}`")

            if st.button(f"📄 View Output #{job['id']}", key=f"output_{job['id']}"):
                output = get_job_output(job["id"])
                st.text_area("Output", output, height=200)

            if st.button(f"🗑️ Remove Job #{job['id']}", key=f"remove_{job['id']}"):
                success, msg = remove_job(job["id"])
                if success:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)
else:
    st.info("📭 Queue is empty. Add commands above to get started!")

# Information section
st.write("---")
st.markdown("""
### ℹ️ How it works:
- put branch name and relax
- it will take a minute
""")
