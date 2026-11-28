<p align="center">
  <img src="fleischers_finest_five_logo.png" alt="Fleischer’s Finest Five group logo" width="100%">
</p>

<div align="center">
  <h1>✨ NEON BANKER’S ALGORITHM ✨</h1>
  <h3>FLEISCHER’S FINEST FIVE · THE BOOP-OOP-A-DOOS</h3>
</div>

<p align="center">
  <strong>A Python desktop simulator for PT 101 Topic 5: Deadlock Avoidance.</strong>
</p>

<p align="center">
  <em>Check the state. Follow the Work. Find a safe sequence.</em>
</p>

---

## 💭 Overview

The Fleischer’s Finest Five Banker’s Algorithm Simulator demonstrates how an operating system can avoid unsafe resource allocations. Enter a system state and follow the Safety Algorithm as it compares each process’s remaining Need with the current Work vector.

The neon nightclub-inspired interface combines a dark purple background with neon pink and cyan accents. Numeric values can be typed or adjusted with buttons, and the calculation appears in tables instead of a plain text dump. An included jazz-style loop and soft button chimes add to the club atmosphere; both can be toggled independently in the header.

### Main Features

| Feature | Description |
| :--- | :--- |
| **Safety Check** | Calculates Available and Need, evaluates possible process completions, and reports a safe sequence or an unsafe state. |
| **Need Matrix** | Displays each process’s Allocation, Max, and calculated Need. |
| **Safety Trace** | Tables each pass, Need-versus-Work comparison, resource release, updated Work, and Finish flags. |
| **Resource Request** | Checks a request against Need and Available, then checks whether a tentative allocation remains safe. |
| **Expanded Results** | Opens the selected result table in a maximized window for easier viewing. |
| **Nightclub Audio** | Plays the included looping jazz track and short button chimes, with separate music and effects controls. |
| **Typed and Button Inputs** | Enter whole numbers directly or use the `−` and `+` controls; the results remain read-only. |
| **Built-in Limits** | Allows 1–8 processes, 1–5 resource types, and 0–99 units, while enforcing Allocation, Max, and Total constraints. |
| **Classroom Example** | Opens with the familiar five-process, three-resource example loaded. |

---

## 📐 Banker’s Algorithm

| Value | Meaning |
| :--- | :--- |
| **Allocation** | Resource units a process currently holds. |
| **Max** | Maximum number of units the process may need. |
| **Need** | `Max − Allocation`, the remaining declared claim. |
| **Available** | `Total − Allocation totals`, the units not currently allocated. |
| **Work** | A changing copy of Available used to simulate process completion. |
| **Finish** | A flag showing whether a process can complete in the simulated order. |

A state is **SAFE** when every process can finish in some order. **UNSAFE** means no safe completion order can be guaranteed; it does not by itself prove that a deadlock has already happened.

---

## 🗂️ Project Structure

    FleischersFinestFive/
    ├── bankers_gui.py
    ├── bankers_simulator.py
    ├── test_bankers_simulator.py
    ├── fleischers_finest_five_logo.png
    ├── nightclub_jazz.wav
    ├── README.md
    ├── USER_GUIDE.md
    ├── TEST_EVIDENCE.md
    └── DEMO_SCRIPT.md

### Main Roles

- `bankers_gui.py` provides the desktop interface, input controls, result tables, and group branding.
- `bankers_simulator.py` implements the data model, Safety Algorithm, request check, and terminal interface.
- `test_bankers_simulator.py` covers safe and unsafe states, requests, and invalid data.
- The Markdown guides explain setup, inputs, test evidence, and the project demonstration.

---

## 🖥️ How to Run

### Requirements

- **Python 3.15** on Windows
- Tkinter, included with the standard Windows Python installer
- No third-party Python packages; the audio controls use Python’s built-in Windows sound module.

### Steps

1. Open the project folder in VS Code.
2. Run the desktop simulator from the VS Code terminal:

       py -3.15 bankers_gui.py

The sample state loads automatically. Choose **Safety Check** or **Resource Request**, then run the calculation. Type a value or use its stepper buttons; press Enter or click an app button to apply typed values.

The terminal version is also available:

       py -3.15 bankers_simulator.py

---

## 📊 Read the Results

- **Need Matrix** shows Allocation, Max, and Need for each process.
- **Safety Trace** begins with the initial Work and Finish state, then shows each process check and Work update. In Finish flags, `✓` means True (finished) and `·` means False (not finished).
- **Request Checks** shows the request comparisons, tentative safety result, and final decision.
- The summary cards show Available, the safe sequence, and the overall status.

---

## 🧪 Run the Checks

Run the included checks from the project root:

       py -3.15 -m unittest -v test_bankers_simulator.py

They cover safe and unsafe states, a granted request, a request that must wait, a request beyond Need, and inconsistent allocation data.

---

## 👥 Team

<table align="center">
  <tr>
    <td align="center"><strong>Justine Garnace</strong><br>Algorithm core &amp; integration</td>
    <td align="center"><strong>Gabriel Leyma</strong><br>Desktop GUI</td>
    <td align="center"><strong>Danielle Madrigal</strong><br>Tests &amp; evidence</td>
    <td align="center"><strong>Harvie Dela Roca</strong><br>README &amp; user guide</td>
    <td align="center"><strong>Mark Verdadero</strong><br>Demo &amp; presentation</td>
  </tr>
</table>

---

## 🙏 Course References &amp; Assistance

The algorithm and terminology follow the course materials supplied for the project: *Final Project – Guideline PT101*, *Deadlock*, and *Chapter 6 – Other sample for Bankers Algorithm*.

Generative AI assisted with parts of the code and documentation. The group should review the final project and follow the course policy for acknowledging assistance.

---

<h2 align="center">🎷 Check the state. Keep the system safe. ✨</h2>
