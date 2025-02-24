import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import Slider, Button
import webbrowser

# Open THEORY.md
def open_theory():
    webbrowser.open("THEORY.md")

# Params
L = 100  # Space (m)
T = 200  # Time steps
dx = 1   # Spatial step (m)
dt = 0.01  # Time step (s)
c = 1.0    # Scaled speed (m/s)
alpha = 0.1  # IP amplitude (m²/kg)
beta = 1e-5  # IP decay (m³/kg)
kappa = 0.2  # Coupling (m⁻¹ s⁻²)
rho_0 = 1e5  # Ref density (kg/m³)
omega = 0.5  # Freq (s⁻¹)
k = 0.1      # Wavenumber (m⁻¹)
gamma = 0.01  # Force scale (m⁻¹)
x_part = 20.0  # Initial pos (m)
v_part = 0.9 * c  # Initial vel (m/s)
q = 1.6e-19    # Charge (C)
m = 9.1e-31    # Mass (kg)

# Grid
x = np.arange(0, L, dx)
t = np.arange(0, T, dt)
X = np.tile(x, (T, 1))
rho = np.zeros((T, L))
U = np.zeros((T, L))
V = np.exp(-((X - L/2)**2) / 200) + 1e5 * np.exp(-((X - L/3)**2) / 10)
part_pos = np.zeros(T)
freq_shift = np.zeros((T, L))  # Match x length

# IP & Fields
def IP(rho, grad_rho, t_idx, x_vals, alpha, beta, omega, k, rho_0):
    phi = omega * t[t_idx] + k * x_vals
    return alpha * np.abs(grad_rho) * np.exp(-beta * rho / rho_0) * np.cos(phi)

def E_field(ip, t_idx):
    return ip * np.sin(omega * t[t_idx])

def B_field(ip, x_vals):
    return ip * np.cos(k * x_vals)

# Initial conditions
rho[0] = np.exp(-((x - L/2)**2) / 200)
U[0] = rho[0]
part_pos[0] = x_part
freq_shift[0] = omega * np.ones(L)  # Initial freq

# Figure
fig, (ax1, ax2, ax3, ax4) = plt.subplots(4, 1, figsize=(10, 16))
plt.subplots_adjust(bottom=0.5)  # Space for widgets
line1, = ax1.plot(x, U[0], 'b-', label='Energy Density (U)')
line2, = ax2.plot(x, rho[0], 'r-', label='Mass Density (ρ)')
line3, = ax3.plot(t[0], part_pos[0], 'g-', label='Particle Position')
line4, = ax4.plot(x, freq_shift[0], 'm-', label='GW Freq Shift')
for ax in [ax1, ax2, ax3, ax4]:
    ax.legend()
ax1.set_xlabel('Space (m)'); ax1.set_ylabel('U (J/m³)')
ax2.set_xlabel('Space (m)'); ax2.set_ylabel('ρ (kg/m³)')
ax3.set_xlabel('Time (s)'); ax3.set_ylabel('Position (m)')
ax3.set_xlim(0, T * dt); ax3.set_ylim(0, L)
ax4.set_xlabel('Space (m)'); ax4.set_ylabel('Freq Shift (s⁻¹)')

# Sliders
ax_alpha = plt.axes([0.25, 0.45, 0.65, 0.03])
ax_beta = plt.axes([0.25, 0.40, 0.65, 0.03])
ax_kappa = plt.axes([0.25, 0.35, 0.65, 0.03])
ax_omega = plt.axes([0.25, 0.30, 0.65, 0.03])
ax_gamma = plt.axes([0.25, 0.25, 0.65, 0.03])
ax_speed = plt.axes([0.25, 0.20, 0.65, 0.03])
s_alpha = Slider(ax_alpha, "Alpha", 0.01, 0.2, valinit=alpha)
s_beta = Slider(ax_beta, "Beta", 1e-6, 1e-4, valinit=beta)
s_kappa = Slider(ax_kappa, "Kappa", 0.1, 0.5, valinit=kappa)
s_omega = Slider(ax_omega, "Omega", 0.1, 1.0, valinit=omega)
s_gamma = Slider(ax_gamma, "Gamma", 0.001, 0.05, valinit=gamma)
s_speed = Slider(ax_speed, "Speed", 0.5, 2.0, valinit=1.0)

# Buttons
ax_reset = plt.axes([0.8, 0.05, 0.1, 0.075])
ax_theory = plt.axes([0.8, 0.15, 0.1, 0.075])
ax_pause = plt.axes([0.8, 0.25, 0.1, 0.075])
ax_snapshot = plt.axes([0.8, 0.35, 0.1, 0.075])
btn_reset = Button(ax_reset, "Reset")
btn_theory = Button(ax_theory, "Theory")
btn_pause = Button(ax_pause, "Pause")
btn_snapshot = Button(ax_snapshot, "Snapshot")

# Solver
def step(t_idx, alpha, beta, kappa, omega, gamma, rho_0, q, m):
    global x_part, v_part
    if t_idx >= 2:
        lap_U = np.zeros(L)
        lap_U[1:-1] = (U[t_idx-1, 2:] - 2 * U[t_idx-1, 1:-1] + U[t_idx-1, :-2]) / dx**2
        grad_rho = np.zeros(L)
        grad_rho[1:-1] = (rho[t_idx-1, 2:] - rho[t_idx-1, :-2]) / (2 * dx)
        ip = IP(rho[t_idx-1], grad_rho, t_idx, x, alpha, beta, omega, k, rho_0)
        source = kappa * ip * np.sin(omega * t[t_idx] + k * x)
        U[t_idx] = 2 * U[t_idx-1] - U[t_idx-2] + dt**2 * (c**2 * lap_U - rho[t_idx-1] * V[t_idx-1] + source)
        U[t_idx] = np.clip(U[t_idx], -1e6, 1e6)
        rho[t_idx] = rho[t_idx-1] + dt * ip
        rho[t_idx] = np.clip(rho[t_idx], 0, 1e6)

        idx = int(x_part / dx)
        if 1 <= idx < len(x) - 1:
            E = E_field(ip[idx], t_idx)
            B = B_field(ip[idx], x[idx])
            F = q * (E + v_part * B) + gamma * ip[idx] * (rho[t_idx, idx] - rho[t_idx-1, idx]) / dt
            a = F / m
            v_part += a * dt
            v_part = np.clip(v_part, -c, c)
            x_part += v_part * dt
            if x_part < 0 or x_part >= L:
                v_part = -v_part
            part_pos[t_idx] = x_part

        freq_shift[t_idx] = omega * (1 + kappa * ip / c)  # Full grid length

# Update
def update(val):
    global alpha, beta, kappa, omega, gamma
    alpha = s_alpha.val
    beta = s_beta.val
    kappa = s_kappa.val
    omega = s_omega.val
    gamma = s_gamma.val

s_alpha.on_changed(update)
s_beta.on_changed(update)
s_kappa.on_changed(update)
s_omega.on_changed(update)
s_gamma.on_changed(update)

# Animation
paused = False
def animate(i):
    if not paused and i < T:
        step(i, alpha, beta, kappa, omega, gamma, rho_0, q, m)
        line1.set_ydata(U[i])
        line2.set_ydata(rho[i])
        line3.set_data(t[:i+1], part_pos[:i+1])
        line4.set_ydata(freq_shift[i])
    return line1, line2, line3, line4

ani = FuncAnimation(fig, animate, frames=T, interval=50, blit=True)

# Button funcs
def reset(event):
    s_alpha.reset(); s_beta.reset(); s_kappa.reset(); s_omega.reset(); s_gamma.reset(); s_speed.reset()
    global rho, U, part_pos, x_part, v_part, freq_shift
    rho = np.zeros((T, L))
    U = np.zeros((T, L))
    part_pos = np.zeros(T)
    freq_shift = np.zeros((T, L))
    rho[0] = np.exp(-((x - L/2)**2) / 200)
    U[0] = rho[0]
    part_pos[0] = 20.0
    v_part = 0.9 * c
    update(None)

def toggle_pause(event):
    global paused
    paused = not paused

def save_snapshot(event):
    fig.savefig("resonance_simulation.png")
    print("Snapshot saved as resonance_simulation.png")

btn_reset.on_clicked(reset)
btn_theory.on_clicked(lambda event: open_theory())
btn_pause.on_clicked(toggle_pause)
btn_snapshot.on_clicked(save_snapshot)

plt.show()
