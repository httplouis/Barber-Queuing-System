"""Admin dashboard for managing the barber queuing system."""
import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from datetime import datetime, timedelta
import time
import requests
import threading
import json
from typing import Dict, Any, List, Optional

# API endpoints
AUTH_API_URL = "http://localhost:8001"
ADMIN_API_URL = "http://localhost:8005"
ANALYTICS_API_URL = "http://localhost:8006"
BOOKING_API_URL = "http://localhost:8000"
BARBER_API_URL = "http://localhost:8004"
FEEDBACK_API_URL = "http://localhost:8002"

# Initialize the app
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("dark-blue")

app = ctk.CTk()
app.geometry("1200x800")
app.title("Admin Dashboard - Barber Queuing System")

# Custom fonts
TITLE_FONT = ctk.CTkFont(family="Helvetica", size=28, weight="bold")
HEADER_FONT = ctk.CTkFont(family="Helvetica", size=20, weight="bold")
NORMAL_FONT = ctk.CTkFont(family="Helvetica", size=14)
BUTTON_FONT = ctk.CTkFont(family="Helvetica", size=14, weight="bold")

# Global variables
current_admin = None
access_token = None
refresh_token = None
current_tab = None
tabs = {}

# Helper function for authenticated requests
def make_authenticated_request(method: str, url: str, **kwargs) -> requests.Response:
    """Make an authenticated HTTP request with JWT token."""
    global access_token
    headers = kwargs.get('headers', {})
    if access_token:
        headers['Authorization'] = f'Bearer {access_token}'
    kwargs['headers'] = headers
    return requests.request(method, url, **kwargs)

# Status message function
def show_status_message(status_label, message: str, color: str = "green", duration: int = 3000):
    """Show a status message."""
    status_label.configure(text=message, text_color=color)
    app.after(duration, lambda: status_label.configure(text=""))

# Login frame
def setup_login_frame():
    """Setup admin login frame."""
    frame = ctk.CTkFrame(app)
    frame.pack(fill="both", expand=True)
    
    title = ctk.CTkLabel(
        frame,
        text="🔐 Admin Dashboard",
        font=TITLE_FONT,
        text_color="#4A90E2"
    )
    title.pack(pady=(100, 20))
    
    subtitle = ctk.CTkLabel(
        frame,
        text="Administrator Login",
        font=HEADER_FONT
    )
    subtitle.pack(pady=(0, 40))
    
    # Username
    username_label = ctk.CTkLabel(frame, text="Username:", font=NORMAL_FONT)
    username_label.pack(pady=(10, 5))
    username_entry = ctk.CTkEntry(frame, width=350, font=NORMAL_FONT, height=40)
    username_entry.pack(pady=(0, 15))
    username_entry.insert(0, "admin")
    
    # Password
    password_label = ctk.CTkLabel(frame, text="Password:", font=NORMAL_FONT)
    password_label.pack(pady=(10, 5))
    password_entry = ctk.CTkEntry(frame, width=350, font=NORMAL_FONT, height=40, show="*")
    password_entry.pack(pady=(0, 20))
    password_entry.insert(0, "admin123")
    
    # Status
    status_label = ctk.CTkLabel(frame, text="", font=NORMAL_FONT, text_color="red")
    status_label.pack(pady=(0, 20))
    
    # Login button
    def login():
        username = username_entry.get()
        password = password_entry.get()
        
        if not username or not password:
            show_status_message(status_label, "Please enter username and password", "red")
            return
        
        status_label.configure(text="Logging in...", text_color="white")
        
        try:
            response = requests.post(
                f"{AUTH_API_URL}/login/",
                json={"username": username, "password": password},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                global current_admin, access_token, refresh_token
                current_admin = data["client"]
                current_admin["client_id"] = data["client_id"]
                access_token = data.get("access_token")
                refresh_token = data.get("refresh_token")
                
                # Check if admin
                if not current_admin.get("is_admin", False):
                    show_status_message(status_label, "Access denied: Admin privileges required", "red")
                    return
                
                show_status_message(status_label, "Login successful!", "green")
                frame.pack_forget()
                setup_dashboard()
            else:
                error_detail = response.json().get("detail", "Invalid credentials")
                show_status_message(status_label, f"Error: {error_detail}", "red")
        except requests.RequestException as e:
            show_status_message(status_label, f"Connection error: {str(e)}", "red")
        except Exception as e:
            show_status_message(status_label, f"Error: {str(e)}", "red")
    
    login_button = ctk.CTkButton(
        frame,
        text="Login",
        command=login,
        width=350,
        height=45,
        font=BUTTON_FONT,
        fg_color="#4A90E2",
        hover_color="#357ABD"
    )
    login_button.pack(pady=(10, 0))
    
    # Info label
    info_label = ctk.CTkLabel(
        frame,
        text="Default: admin / admin123",
        font=ctk.CTkFont(size=12),
        text_color="gray"
    )
    info_label.pack(pady=(20, 0))

# Dashboard setup
def setup_dashboard():
    """Setup main admin dashboard with tabs."""
    # Create tabview
    tabview = ctk.CTkTabview(app, width=1180, height=750)
    tabview.pack(fill="both", expand=True, padx=10, pady=10)
    
    # Create tabs
    tabs["overview"] = tabview.add("📊 Overview")
    tabs["queue"] = tabview.add("⏱️ Queue Management")
    tabs["barbers"] = tabview.add("👨‍💼 Barber Management")
    tabs["bookings"] = tabview.add("📅 Bookings")
    tabs["users"] = tabview.add("👥 Users")
    tabs["analytics"] = tabview.add("📈 Analytics")
    
    setup_overview_tab()
    setup_queue_tab()
    setup_barbers_tab()
    setup_bookings_tab()
    setup_users_tab()
    setup_analytics_tab()

def setup_overview_tab():
    """Setup overview/dashboard tab."""
    frame = tabs["overview"]
    
    # Title
    title = ctk.CTkLabel(
        frame,
        text="Dashboard Overview",
        font=TITLE_FONT,
        text_color="#4A90E2"
    )
    title.pack(pady=(20, 30))
    
    # Stats container
    stats_container = ctk.CTkFrame(frame, fg_color="transparent")
    stats_container.pack(pady=20, fill="x", padx=20)
    
    # Stats cards
    stats_cards = {}
    
    def create_stat_card(parent, row, col, title_text, value_text, color="#4A90E2"):
        """Create a statistics card."""
        card = ctk.CTkFrame(parent, width=250, height=150, corner_radius=15)
        card.grid(row=row, column=col, padx=15, pady=15, sticky="nsew")
        
        title_label = ctk.CTkLabel(
            card,
            text=title_text,
            font=NORMAL_FONT,
            text_color="gray"
        )
        title_label.pack(pady=(20, 10))
        
        value_label = ctk.CTkLabel(
            card,
            text=value_text,
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color=color
        )
        value_label.pack()
        
        return value_label
    
    # Create stat cards
    stats_cards["total_bookings"] = create_stat_card(
        stats_container, 0, 0, "Total Bookings", "0", "#4A90E2"
    )
    stats_cards["queue_length"] = create_stat_card(
        stats_container, 0, 1, "Queue Length", "0", "#10B981"
    )
    stats_cards["total_clients"] = create_stat_card(
        stats_container, 0, 2, "Total Clients", "0", "#F59E0B"
    )
    stats_cards["total_barbers"] = create_stat_card(
        stats_container, 0, 3, "Active Barbers", "0", "#EF4444"
    )
    
    # Refresh button
    def refresh_stats():
        """Refresh dashboard statistics."""
        try:
            response = make_authenticated_request(
                "GET",
                f"{ADMIN_API_URL}/dashboard/stats"
            )
            
            if response.status_code == 200:
                stats = response.json()
                stats_cards["total_bookings"].configure(
                    text=str(stats.get("total_bookings", 0))
                )
                stats_cards["queue_length"].configure(
                    text=str(stats.get("queue_length", 0))
                )
                stats_cards["total_clients"].configure(
                    text=str(stats.get("total_clients", 0))
                )
                stats_cards["total_barbers"].configure(
                    text=str(stats.get("available_barbers", 0))
                )
        except Exception as e:
            print(f"Error refreshing stats: {e}")
    
    refresh_button = ctk.CTkButton(
        frame,
        text="🔄 Refresh Stats",
        command=refresh_stats,
        width=200,
        font=BUTTON_FONT
    )
    refresh_button.pack(pady=20)
    
    # Initial refresh
    refresh_stats()
    
    # Auto-refresh every 30 seconds
    def auto_refresh():
        refresh_stats()
        app.after(30000, auto_refresh)
    
    app.after(30000, auto_refresh)

def setup_queue_tab():
    """Setup queue management tab."""
    frame = tabs["queue"]
    
    title = ctk.CTkLabel(
        frame,
        text="Queue Management",
        font=TITLE_FONT,
        text_color="#4A90E2"
    )
    title.pack(pady=(20, 20))
    
    # Queue display
    queue_frame = ctk.CTkFrame(frame)
    queue_frame.pack(fill="both", expand=True, padx=20, pady=10)
    
    # Table
    table_frame = ttk.Frame(queue_frame)
    table_frame.pack(fill="both", expand=True, padx=10, pady=10)
    
    columns = ("Position", "Client ID", "Status", "Timestamp", "Estimated Wait")
    queue_table = ttk.Treeview(table_frame, columns=columns, show="headings", height=20)
    
    for col in columns:
        queue_table.heading(col, text=col)
        queue_table.column(col, width=150, anchor="center")
    
    queue_table.pack(side="left", fill="both", expand=True)
    
    scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=queue_table.yview)
    queue_table.configure(yscroll=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    
    # Refresh function
    def refresh_queue():
        """Refresh queue display."""
        for row in queue_table.get_children():
            queue_table.delete(row)
        
        try:
            response = make_authenticated_request(
                "GET",
                f"{ADMIN_API_URL}/queue/manage"
            )
            
            if response.status_code == 200:
                data = response.json()
                queue = data.get("queue", [])
                
                sorted_queue = sorted(
                    queue,
                    key=lambda x: x.get("timestamp", "")
                )
                
                for i, entry in enumerate(sorted_queue, 1):
                    queue_table.insert("", "end", values=(
                        i,
                        entry.get("client_id", ""),
                        entry.get("status", "").upper(),
                        entry.get("timestamp", ""),
                        f"{entry.get('estimated_wait', 0)} min"
                    ))
        except Exception as e:
            print(f"Error refreshing queue: {e}")
    
    refresh_button = ctk.CTkButton(
        frame,
        text="🔄 Refresh Queue",
        command=refresh_queue,
        width=200,
        font=BUTTON_FONT
    )
    refresh_button.pack(pady=10)
    
    refresh_queue()
    app.after(10000, lambda: app.after(10000, refresh_queue))

def setup_barbers_tab():
    """Setup barber management tab."""
    frame = tabs["barbers"]
    
    title = ctk.CTkLabel(
        frame,
        text="Barber Management",
        font=TITLE_FONT,
        text_color="#4A90E2"
    )
    title.pack(pady=(20, 20))
    
    # Barbers list
    barbers_frame = ctk.CTkFrame(frame)
    barbers_frame.pack(fill="both", expand=True, padx=20, pady=10)
    
    table_frame = ttk.Frame(barbers_frame)
    table_frame.pack(fill="both", expand=True, padx=10, pady=10)
    
    columns = ("ID", "Name", "Specialties", "Available")
    barbers_table = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)
    
    for col in columns:
        barbers_table.heading(col, text=col)
        barbers_table.column(col, width=200, anchor="center")
    
    barbers_table.pack(side="left", fill="both", expand=True)
    
    scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=barbers_table.yview)
    barbers_table.configure(yscroll=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    
    # Add barber form
    form_frame = ctk.CTkFrame(frame)
    form_frame.pack(pady=20, padx=20, fill="x")
    
    name_label = ctk.CTkLabel(form_frame, text="Barber Name:", font=NORMAL_FONT)
    name_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
    name_entry = ctk.CTkEntry(form_frame, width=300, font=NORMAL_FONT)
    name_entry.grid(row=0, column=1, padx=10, pady=10)
    
    def add_barber():
        """Add a new barber."""
        name = name_entry.get()
        if not name:
            return
        
        try:
            response = requests.post(
                f"{BARBER_API_URL}/barbers/",
                json={"name": name, "specialties": [], "available": True},
                timeout=5
            )
            
            if response.status_code == 200:
                name_entry.delete(0, tk.END)
                refresh_barbers()
        except Exception as e:
            print(f"Error adding barber: {e}")
    
    add_button = ctk.CTkButton(
        form_frame,
        text="➕ Add Barber",
        command=add_barber,
        width=150,
        font=BUTTON_FONT
    )
    add_button.grid(row=0, column=2, padx=10, pady=10)
    
    def refresh_barbers():
        """Refresh barbers list."""
        for row in barbers_table.get_children():
            barbers_table.delete(row)
        
        try:
            response = requests.get(f"{BARBER_API_URL}/barbers/", timeout=5)
            if response.status_code == 200:
                data = response.json()
                barbers = data.get("barbers", [])
                
                for barber in barbers:
                    specialties = ", ".join(barber.get("specialties", []))
                    available = "Yes" if barber.get("available", False) else "No"
                    barbers_table.insert("", "end", values=(
                        barber.get("barber_id", ""),
                        barber.get("name", ""),
                        specialties,
                        available
                    ))
        except Exception as e:
            print(f"Error refreshing barbers: {e}")
    
    refresh_button = ctk.CTkButton(
        frame,
        text="🔄 Refresh",
        command=refresh_barbers,
        width=200,
        font=BUTTON_FONT
    )
    refresh_button.pack(pady=10)
    
    refresh_barbers()

def setup_bookings_tab():
    """Setup bookings management tab."""
    frame = tabs["bookings"]
    
    title = ctk.CTkLabel(
        frame,
        text="Bookings Management",
        font=TITLE_FONT,
        text_color="#4A90E2"
    )
    title.pack(pady=(20, 20))
    
    # Bookings table
    bookings_frame = ctk.CTkFrame(frame)
    bookings_frame.pack(fill="both", expand=True, padx=20, pady=10)
    
    table_frame = ttk.Frame(bookings_frame)
    table_frame.pack(fill="both", expand=True, padx=10, pady=10)
    
    columns = ("ID", "Client ID", "Barber ID", "Service", "Date", "Time", "Status")
    bookings_table = ttk.Treeview(table_frame, columns=columns, show="headings", height=20)
    
    for col in columns:
        bookings_table.heading(col, text=col)
        bookings_table.column(col, width=120, anchor="center")
    
    bookings_table.pack(side="left", fill="both", expand=True)
    
    scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=bookings_table.yview)
    bookings_table.configure(yscroll=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    
    def refresh_bookings():
        """Refresh bookings list."""
        for row in bookings_table.get_children():
            bookings_table.delete(row)
        
        try:
            response = make_authenticated_request(
                "GET",
                f"{ADMIN_API_URL}/bookings/all"
            )
            
            if response.status_code == 200:
                data = response.json()
                bookings = data.get("bookings", [])
                
                for booking in bookings:
                    bookings_table.insert("", "end", values=(
                        booking.get("booking_id", ""),
                        booking.get("client_id", ""),
                        booking.get("barber_id", ""),
                        booking.get("service_type", ""),
                        booking.get("booking_date", ""),
                        booking.get("booking_time", ""),
                        booking.get("status", "")
                    ))
        except Exception as e:
            print(f"Error refreshing bookings: {e}")
    
    refresh_button = ctk.CTkButton(
        frame,
        text="🔄 Refresh Bookings",
        command=refresh_bookings,
        width=200,
        font=BUTTON_FONT
    )
    refresh_button.pack(pady=10)
    
    refresh_bookings()

def setup_users_tab():
    """Setup user management tab."""
    frame = tabs["users"]
    
    title = ctk.CTkLabel(
        frame,
        text="User Management",
        font=TITLE_FONT,
        text_color="#4A90E2"
    )
    title.pack(pady=(20, 20))
    
    # Users table
    users_frame = ctk.CTkFrame(frame)
    users_frame.pack(fill="both", expand=True, padx=20, pady=10)
    
    table_frame = ttk.Frame(users_frame)
    table_frame.pack(fill="both", expand=True, padx=10, pady=10)
    
    columns = ("ID", "Username", "Name", "Email", "Phone", "Admin", "Registered")
    users_table = ttk.Treeview(table_frame, columns=columns, show="headings", height=20)
    
    for col in columns:
        users_table.heading(col, text=col)
        users_table.column(col, width=120, anchor="center")
    
    users_table.pack(side="left", fill="both", expand=True)
    
    scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=users_table.yview)
    users_table.configure(yscroll=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    
    def refresh_users():
        """Refresh users list."""
        for row in users_table.get_children():
            users_table.delete(row)
        
        try:
            response = make_authenticated_request(
                "GET",
                f"{ADMIN_API_URL}/clients/all"
            )
            
            if response.status_code == 200:
                data = response.json()
                clients = data.get("clients", [])
                
                for client in clients:
                    users_table.insert("", "end", values=(
                        client.get("client_id", ""),
                        client.get("username", ""),
                        client.get("name", ""),
                        client.get("email", ""),
                        client.get("phone", ""),
                        "Yes" if client.get("is_admin", False) else "No",
                        client.get("registered_at", "")[:10] if client.get("registered_at") else ""
                    ))
        except Exception as e:
            print(f"Error refreshing users: {e}")
    
    refresh_button = ctk.CTkButton(
        frame,
        text="🔄 Refresh Users",
        command=refresh_users,
        width=200,
        font=BUTTON_FONT
    )
    refresh_button.pack(pady=10)
    
    refresh_users()

def setup_analytics_tab():
    """Setup analytics tab."""
    frame = tabs["analytics"]
    
    title = ctk.CTkLabel(
        frame,
        text="Analytics & Reports",
        font=TITLE_FONT,
        text_color="#4A90E2"
    )
    title.pack(pady=(20, 20))
    
    # Analytics container
    analytics_container = ctk.CTkFrame(frame, fg_color="transparent")
    analytics_container.pack(fill="both", expand=True, padx=20, pady=10)
    
    # Popular services
    services_frame = ctk.CTkFrame(analytics_container)
    services_frame.pack(fill="both", expand=True, padx=10, pady=10)
    
    services_title = ctk.CTkLabel(
        services_frame,
        text="Popular Services",
        font=HEADER_FONT
    )
    services_title.pack(pady=(10, 10))
    
    services_table = ttk.Treeview(
        services_frame,
        columns=("Service", "Bookings", "Revenue"),
        show="headings",
        height=10
    )
    
    services_table.heading("Service", text="Service")
    services_table.heading("Bookings", text="Bookings")
    services_table.heading("Revenue", text="Revenue ($)")
    
    services_table.column("Service", width=300)
    services_table.column("Bookings", width=150)
    services_table.column("Revenue", width=150)
    
    services_table.pack(fill="both", expand=True, padx=10, pady=10)
    
    # Barber performance
    barbers_frame = ctk.CTkFrame(analytics_container)
    barbers_frame.pack(fill="both", expand=True, padx=10, pady=10)
    
    barbers_title = ctk.CTkLabel(
        barbers_frame,
        text="Barber Performance",
        font=HEADER_FONT
    )
    barbers_title.pack(pady=(10, 10))
    
    barbers_table = ttk.Treeview(
        barbers_frame,
        columns=("Barber", "Rating", "Ratings Count", "Bookings"),
        show="headings",
        height=10
    )
    
    barbers_table.heading("Barber", text="Barber")
    barbers_table.heading("Rating", text="Avg Rating")
    barbers_table.heading("Ratings Count", text="Ratings")
    barbers_table.heading("Bookings", text="Bookings")
    
    barbers_table.column("Barber", width=250)
    barbers_table.column("Rating", width=120)
    barbers_table.column("Ratings Count", width=120)
    barbers_table.column("Bookings", width=120)
    
    barbers_table.pack(fill="both", expand=True, padx=10, pady=10)
    
    def refresh_analytics():
        """Refresh analytics data."""
        # Clear tables
        for row in services_table.get_children():
            services_table.delete(row)
        for row in barbers_table.get_children():
            barbers_table.delete(row)
        
        try:
            # Get popular services
            response = make_authenticated_request(
                "GET",
                f"{ANALYTICS_API_URL}/analytics/popular-services"
            )
            
            if response.status_code == 200:
                data = response.json()
                services = data.get("popular_services", [])
                
                for service in services:
                    services_table.insert("", "end", values=(
                        service.get("service_name", ""),
                        service.get("booking_count", 0),
                        f"${service.get('revenue', 0):.2f}"
                    ))
            
            # Get barber performance
            response = make_authenticated_request(
                "GET",
                f"{ANALYTICS_API_URL}/analytics/barber-performance"
            )
            
            if response.status_code == 200:
                data = response.json()
                barbers = data.get("barber_performance", [])
                
                for barber in barbers:
                    barbers_table.insert("", "end", values=(
                        barber.get("barber_name", ""),
                        f"{barber.get('average_rating', 0):.2f} ⭐",
                        barber.get("total_ratings", 0),
                        barber.get("total_bookings", 0)
                    ))
        except Exception as e:
            print(f"Error refreshing analytics: {e}")
    
    refresh_button = ctk.CTkButton(
        frame,
        text="🔄 Refresh Analytics",
        command=refresh_analytics,
        width=200,
        font=BUTTON_FONT
    )
    refresh_button.pack(pady=10)
    
    refresh_analytics()

# Start with login
setup_login_frame()

# Run the app
if __name__ == "__main__":
    app.mainloop()

