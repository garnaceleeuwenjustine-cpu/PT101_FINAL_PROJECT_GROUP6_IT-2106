# Five-Member GitHub Commit Guide

This is Group 6, **Fleischer’s Finest Five**, also known as **The Boop-Oop-A-Doos**. The PT 101 topic is **Topic 5: Deadlock Avoidance — Banker’s Algorithm**.

## One file assignment per member

Use the five member commit packs supplied with the project. Each pack contains only that member’s assigned project files. Extract the files directly into the repository root; do not add an extra member folder.

| Member | Assigned project files |
|---|---|
| GARNACE, JUSTINE LEEUWEN P. | `bankers_gui.py`, `fleischers_finest_five_logo.png` |
| LEYMA, GABRIEL U. | `bankers_simulator.py` |
| MADRIGAL, DANIELLE LAWRENCE A. | `test_bankers_simulator.py`, `TEST_EVIDENCE.md` |
| DELA ROCA, HARVIE S. | `README.md`, `USER_GUIDE.md` |
| VERDADERO, MARK LIESTER M. | `.gitignore`, `CONTRIBUTION_PLAN.md`, `CONTRIBUTING.md`, `DEMO_SCRIPT.md` |

The source files are divided among the five members exactly once. After all five contributions are merged, the GUI and algorithm module will be together in the repository root and the project will be runnable.

## Repository owner: create and invite

1. Create a GitHub repository and add an initial README so GitHub creates the `main` branch.
2. Open **Settings → Collaborators** and invite the other four members’ GitHub usernames with **Write** access.
3. Each member accepts their invite before cloning the repository.

## Each member: make a separate commit

Clone the repository and make a task branch:

```text
git clone <repository-url>
cd <repository-name>
git switch -c <your-name>/<short-task>
```

Extract your pack’s files into this repository folder. Stage only your assigned file names, then commit and push:

```text
git add <your-assigned-file-names>
git commit -m "Describe your contribution"
git push -u origin <your-name>/<short-task>
```

Open a pull request so another member can review it, then merge it into `main`. The next member should start from the updated `main` branch. This keeps each member’s contribution in its own commit and shows the contributor’s GitHub account.

Set your personal Git identity once on your computer, using the email connected to your own GitHub account:

```text
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

Do not share account passwords or personal access tokens.
