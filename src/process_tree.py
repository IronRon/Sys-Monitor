import psutil
# This won't be part of the continuous monitor yet. It's a little systems exploration utility.
# Chromium's own documentation describes the main browser process spawning renderer, GPU and other child processes and using IPC between them

def get_process_role(process):
    try:
        command_line = process.cmdline()

        for argument in command_line:
            if argument.startswith("--type="):
                return argument.split("=", 1)[1]

        return "browser"

    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return "unknown"


def print_tree(process, prefix=""):
    try:
        role = get_process_role(process)

        print(
            f"{prefix}"
            f"{process.name()} "
            f"[PID {process.pid}] "
            f"({role})"
        )

        children = process.children()

        for index, child in enumerate(children):
            is_last = index == len(children) - 1

            branch = "└── " if is_last else "├── "

            child_prefix = (
                prefix + ("    " if is_last else "│   ")
            )

            print(
                f"{prefix}{branch}",
                end=""
            )

            print_tree(
                child,
                child_prefix,
            )

    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return


def find_chrome_roots():
    chrome_processes = []

    for process in psutil.process_iter(
        ["pid", "ppid", "name"],
        ad_value=None,
    ):
        if (
            process.info["name"]
            and process.info["name"].lower() == "chrome.exe"
        ):
            chrome_processes.append(process)

    chrome_pids = {
        process.pid
        for process in chrome_processes
    }

    roots = []

    for process in chrome_processes:
        try:
            if process.ppid() not in chrome_pids:
                roots.append(process)

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    return roots


def main():
    roots = find_chrome_roots()

    if not roots:
        print("Chrome is not currently running.")
        return

    for root in roots:
        print_tree(root)
        print()


if __name__ == "__main__":
    main()