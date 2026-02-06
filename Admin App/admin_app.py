"""
Aplicación de Administración para Sistema de Reservas de Cancha de Tenis
Gestión de reservas, usuarios y créditos
"""

import streamlit as st
from admin_auth import admin_auth_manager, require_admin_auth
from admin_database import admin_db_manager
from database_manager import SupabaseManager
from timezone_utils import get_colombia_now, get_colombia_today, format_date_display
from email_config import email_manager
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from collections import defaultdict
import time


# ============================================
# CACHED DATA FUNCTIONS FOR PERFORMANCE
# ============================================

@st.cache_data(ttl=60)
def get_cached_system_statistics():
    """Cached system statistics - TTL 60 seconds"""
    return admin_db_manager.get_system_statistics()

@st.cache_data(ttl=300)
def get_cached_heatmap_data(days_filter):
    """Cached heatmap data - TTL 5 minutes"""
    return admin_db_manager.get_heatmap_data(days_filter)

@st.cache_data(ttl=120)
def get_cached_occupancy_data(scale, offset):
    """Cached occupancy data - TTL 2 minutes"""
    return admin_db_manager.get_occupancy_data(scale, offset)

@st.cache_data(ttl=600)
def get_cached_historic_average_occupancy():
    """Cached historic average - TTL 10 minutes"""
    return admin_db_manager.get_historic_average_occupancy()

@st.cache_data(ttl=300)
def get_cached_user_reservation_statistics():
    """Cached user stats for leaderboard - TTL 5 minutes"""
    return admin_db_manager.get_user_reservation_statistics()

@st.cache_data(ttl=120)
def get_cached_weekly_calendar_data(week_offset):
    """Cached calendar data - TTL 2 minutes"""
    return admin_db_manager.get_weekly_calendar_data(week_offset)

@st.cache_data(ttl=120)
def get_cached_alerts_and_anomalies():
    """Cached alerts - TTL 2 minutes"""
    return admin_db_manager.get_alerts_and_anomalies()

@st.cache_data(ttl=120)
def get_cached_cancellation_statistics(days_back):
    """Cached cancellation stats - TTL 2 minutes"""
    return admin_db_manager.get_cancellation_statistics(days_back)

@st.cache_data(ttl=600)
def get_cached_user_retention_data():
    """Cached retention data - TTL 10 minutes"""
    return admin_db_manager.get_user_retention_data()

@st.cache_data(ttl=300)
def get_cached_credit_statistics():
    """Cached credit statistics - TTL 5 minutes"""
    return admin_db_manager.get_credit_statistics()

@st.cache_data(ttl=120)
def get_cached_credit_economy_data(days_back):
    """Cached credit economy data - TTL 2 minutes"""
    return admin_db_manager.get_credit_economy_data(days_back)

@st.cache_data(ttl=300)
def get_cached_users_detailed_statistics(limit: int = None, offset: int = 0):
    """Cached users detailed stats - TTL 5 minutes"""
    return admin_db_manager.get_users_detailed_statistics(limit=limit, offset=offset)

@st.cache_data(ttl=300)
def get_cached_users_count():
    """Cached users count - TTL 5 minutes"""
    return admin_db_manager.get_users_count()

@st.cache_data(ttl=30)
def get_cached_search_users(search_term: str):
    """Cached user search - TTL 30 seconds"""
    return admin_db_manager.search_users_detailed(search_term)

@st.cache_data(ttl=60)
def get_cached_dashboard_data():
    """
    Batch function to get all dashboard data in one call.
    Returns dict with all data needed for dashboard tab.
    TTL 60 seconds.
    """
    return {
        'stats': admin_db_manager.get_system_statistics(),
        'user_stats': admin_db_manager.get_user_reservation_statistics(),
        'historic_avg': admin_db_manager.get_historic_average_occupancy(),
        'alerts': admin_db_manager.get_alerts_and_anomalies()
    }


# Colores US Open
US_OPEN_BLUE = "#001854"
US_OPEN_LIGHT_BLUE = "#2478CC"
US_OPEN_YELLOW = "#FFD400"


def setup_admin_page_config():
    """Configurar la página de administración"""
    st.set_page_config(
        page_title="Admin - Reservas Tenis",
        page_icon="⚙️",
        layout="wide",
        initial_sidebar_state="expanded"
    )

def apply_admin_styles():
    """Aplicar estilos CSS para la interfaz de administración"""
    st.markdown(f"""
    <style>
    .admin-header {{
        background: linear-gradient(135deg, {US_OPEN_BLUE} 0%, {US_OPEN_LIGHT_BLUE} 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 20px;
    }}

    .stat-card {{
        background: white;
        border: 2px solid {US_OPEN_LIGHT_BLUE};
        border-radius: 12px;
        padding: 20px;
        margin: 10px 0;
        text-align: center;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }}

    .stat-number {{
        font-size: 2rem;
        font-weight: bold;
        color: {US_OPEN_BLUE};
    }}

    .stat-label {{
        color: #666;
        font-size: 0.9rem;
        margin-top: 5px;
    }}

    .success-card {{
        background: #e8f5e8;
        border: 2px solid #4CAF50;
        border-radius: 12px;
        padding: 15px;
        margin: 10px 0;
        color: #2e7d32;
    }}

    .warning-card {{
        background: #fff3cd;
        border: 2px solid #ffc107;
        border-radius: 12px;
        padding: 15px;
        margin: 10px 0;
        color: #856404;
    }}

    .error-card {{
        background: #f8d7da;
        border: 2px solid #dc3545;
        border-radius: 12px;
        padding: 15px;
        margin: 10px 0;
        color: #721c24;
    }}

    /* Segmented control styling */
    .stSegmentedControl > div {{
        background-color: white;
        border-radius: 8px;
        border: 2px solid {US_OPEN_LIGHT_BLUE};
        margin: 10px 0;
    }}

    .stSegmentedControl button {{
        color: {US_OPEN_BLUE} !important;
        font-weight: 500 !important;
    }}

    .stSegmentedControl button[aria-selected="true"] {{
        background-color: {US_OPEN_LIGHT_BLUE} !important;
        color: white !important;
        font-weight: bold !important;
    }}
    
    /* Mejorar estilo de expanders */
    .streamlit-expanderHeader {{
        font-size: 1.1rem !important;
        font-weight: 600 !important;
    }}
    
    .streamlit-expanderContent {{
        padding: 12px 16px !important;
    }}
    </style>
    """, unsafe_allow_html=True)

def show_admin_login():
    """Mostrar interfaz de login de administrador"""
    st.markdown("""
    <div class="admin-header">
        <h1>🔐 Acceso de Administrador</h1>
        <p>Sistema de Gestión de Reservas de Cancha de Tenis</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        with st.form("admin_login_form"):
            st.markdown("### 👤 Iniciar Sesión")

            username = st.text_input(
                "Usuario",
                placeholder="Ingresa tu usuario administrativo"
            )

            password = st.text_input(
                "Contraseña",
                type="password",
                placeholder="Ingresa tu contraseña"
            )

            login_button = st.form_submit_button(
                "Iniciar Sesión",
                type="primary",
                use_container_width=True
            )

            if login_button:
                if admin_auth_manager.login_admin(username, password):
                    st.success("✅ Acceso concedido")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("❌ Credenciales incorrectas")

def show_admin_dashboard():
    """Mostrar el panel principal de administración"""
    admin_user = st.session_state.get('admin_user')

    # Header con información del admin
    st.markdown(f"""
    <div class="admin-header">
        <h1>⚙️ Panel de Administración</h1>
        <p>Bienvenido, {admin_user['full_name']}</p>
    </div>
    """, unsafe_allow_html=True)

    # Barra superior mejorada
    st.markdown("""
    <div style="background: rgba(255,255,255,0.1); border-radius: 12px; padding: 15px; margin: 15px 0; 
                backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.2);">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div style="color: white; opacity: 0.9;">
                <i class="fas fa-clock"></i> <span style="font-size: 14px;">Última actualización: {}</span>
            </div>
        </div>
    </div>
    """.format(get_colombia_now().strftime('%d/%m/%Y %H:%M:%S')), unsafe_allow_html=True)

    # Controles de acción
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

    with col2:
        if st.button("🔄 Actualizar", type="secondary", use_container_width=True):
            st.cache_data.clear()
            st.success("✅ Datos actualizados")
            st.rerun()

    with col3:
        if st.button("📊 Exportar", type="secondary", use_container_width=True):
            with st.spinner("📊 Generando archivo Excel..."):
                try:
                    # Obtener datos
                    users_data = admin_db_manager.get_all_users_for_export()
                    reservations_data = admin_db_manager.get_all_reservations_for_export()
                    credits_data = admin_db_manager.get_credit_transactions_for_export()

                    # Crear archivo Excel
                    from io import BytesIO

                    # Crear buffer en memoria
                    buffer = BytesIO()

                    # Crear archivo Excel con múltiples hojas
                    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                        # Hoja de usuarios
                        if users_data:
                            df_users = pd.DataFrame(users_data)
                            df_users.to_excel(writer, sheet_name='Usuarios', index=False)

                        # Hoja de reservas
                        if reservations_data:
                            df_reservations = pd.DataFrame(reservations_data)
                            df_reservations.to_excel(writer, sheet_name='Reservas', index=False)

                        # Hoja de créditos
                        if credits_data:
                            df_credits = pd.DataFrame(credits_data)
                            df_credits.to_excel(writer, sheet_name='Créditos', index=False)

                    buffer.seek(0)

                    # Generar nombre de archivo con fecha
                    fecha_actual = get_colombia_now().strftime('%Y%m%d_%H%M%S')
                    filename = f"reservas_tenis_export_{fecha_actual}.xlsx"

                    # Botón de descarga
                    st.download_button(
                        label="📥 Descargar Excel",
                        data=buffer.getvalue(),
                        file_name=filename,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        type="primary"
                    )

                    st.success(
                        f"✅ Archivo generado: {len(users_data)} usuarios, {len(reservations_data)} reservas, {len(credits_data)} transacciones")

                except Exception as e:
                    st.error(f"❌ Error generando archivo: {str(e)}")

    with col4:
        if st.button("🚪 Cerrar Sesión", type="primary", use_container_width=True):
            admin_auth_manager.logout_admin()
            st.rerun()

    st.divider()


    # Control de navegación segmentado
    previous_tab = st.session_state.get('admin_current_tab', "📊 Dashboard")

    tab = st.segmented_control(
        "Navegación Admin",
        ["📊 Dashboard", "📅 Reservas", "👥 Usuarios", "💰 Créditos", "🔧 Mantenimiento", "⚙️ Config"],
        selection_mode="single",
        default="📊 Dashboard",
        label_visibility="collapsed",
    )

    # Limpiar búsquedas si cambió de pestaña
    if tab != previous_tab:
        # Limpiar estados de búsqueda
        if 'selected_user_for_reservations' in st.session_state:
            del st.session_state.selected_user_for_reservations
        if 'found_users' in st.session_state:
            del st.session_state.found_users

        # Guardar pestaña actual
        st.session_state.admin_current_tab = tab

    # Mostrar sección correspondiente
    if tab == "📊 Dashboard":
        show_dashboard_tab()
    elif tab == "📅 Reservas":
        show_reservations_management_tab()
    elif tab == "👥 Usuarios":
        show_users_management_tab()
    elif tab == "💰 Créditos":
        show_credits_management_tab()
    elif tab == "🔧 Mantenimiento":
        show_maintenance_tab()
    elif tab == "⚙️ Config":
        show_config_tab()

def show_dashboard_tab():
    """Mostrar estadísticas y dashboard"""
    st.subheader("📊 Dashboard & Estadísticas")

    # Obtener estadísticas (cached for performance)
    stats = get_cached_system_statistics()

    # Métricas principales - Una fila: RESERVAS Y OCUPACIÓN
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{stats['total_reservations']}</div>
            <div class="stat-label">Total Reservas</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{stats['week_reservations']}</div>
            <div class="stat-label">Reservas Esta Semana</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        # Color de ocupación según porcentaje
        occupancy = stats['today_occupancy_rate']
        occupancy_color = '#2e7d32' if occupancy >= 70 else '#f57c00' if occupancy >= 40 else '#757575'
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number" style="color: {occupancy_color};">{occupancy}%</div>
            <div class="stat-label">Ocupación Hoy</div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # ========================================
    # ANALYTICS SECTION
    # ========================================
    st.markdown("### 📈 Reservas de Usuarios")

    # Initialize database manager for analytics
    db_manager = SupabaseManager()

    # Date range selector in a clean layout
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        # Default to 30 days ago
        default_start = (get_colombia_today() - timedelta(days=30))
        start_date = st.date_input(
            "📅 Fecha de inicio",
            value=default_start,
            max_value=get_colombia_today(),
            key="analytics_start_date"
        )

    with col2:
        end_date = st.date_input(
            "📅 Fecha de fin",
            value=get_colombia_today(),
            max_value=get_colombia_today(),
            key="analytics_end_date"
        )

    with col3:
        granularity = st.selectbox(
            "📊 Nivel de detalle",
            ["Hora", "Día", "Mes"],
            index=1,
            key="analytics_granularity"
        )

    granularity_map = {"Hora": "hour", "Día": "day", "Mes": "month"}
    selected_granularity = granularity_map[granularity]

    # Validate and fetch data
    if start_date <= end_date:
        try:
            # Calculate period duration for comparison
            period_days = (end_date - start_date).days + 1
            prev_end_date = start_date - timedelta(days=1)
            prev_start_date = prev_end_date - timedelta(days=period_days - 1)

            # Get activity timeline data for current period
            timeline_data = db_manager.get_activity_timeline_data(
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d')
            )

            # Get activity timeline data for previous period (for comparison)
            prev_timeline_data = db_manager.get_activity_timeline_data(
                start_date=prev_start_date.strftime('%Y-%m-%d'),
                end_date=prev_end_date.strftime('%Y-%m-%d')
            )

            if timeline_data and len(timeline_data) > 0:
                # Process data for timeline
                df_timeline = pd.DataFrame(timeline_data)
                df_timeline['created_at'] = pd.to_datetime(df_timeline['created_at'])

                # Create time bucket based on granularity
                if selected_granularity == 'hour':
                    df_timeline['time_bucket'] = df_timeline['created_at'].dt.floor('H')
                    time_format = '%Y-%m-%d %H:%M'
                elif selected_granularity == 'day':
                    df_timeline['time_bucket'] = df_timeline['created_at'].dt.floor('D')
                    time_format = '%Y-%m-%d'
                else:  # month
                    df_timeline['time_bucket'] = df_timeline['created_at'].dt.to_period('M').dt.to_timestamp()
                    time_format = '%Y-%m'

                # Count activities per time bucket
                activity_counts = df_timeline.groupby('time_bucket').agg({
                    'id': 'count',
                    'user_id': 'nunique'
                }).reset_index()
                activity_counts.columns = ['time_bucket', 'total_activities', 'unique_users']

                # Process previous period data for comparison
                prev_activity_counts = None
                if prev_timeline_data and len(prev_timeline_data) > 0:
                    df_prev = pd.DataFrame(prev_timeline_data)
                    df_prev['created_at'] = pd.to_datetime(df_prev['created_at'])

                    if selected_granularity == 'hour':
                        df_prev['time_bucket'] = df_prev['created_at'].dt.floor('H')
                    elif selected_granularity == 'day':
                        df_prev['time_bucket'] = df_prev['created_at'].dt.floor('D')
                    else:
                        df_prev['time_bucket'] = df_prev['created_at'].dt.to_period('M').dt.to_timestamp()

                    prev_activity_counts = df_prev.groupby('time_bucket').agg({
                        'id': 'count'
                    }).reset_index()
                    prev_activity_counts.columns = ['time_bucket', 'total_activities']

                    # Shift previous period dates to align with current period for comparison
                    prev_activity_counts['time_bucket_shifted'] = prev_activity_counts['time_bucket'] + timedelta(days=period_days)

                # Calculate trend
                current_total = activity_counts['total_activities'].sum()
                prev_total = prev_activity_counts['total_activities'].sum() if prev_activity_counts is not None else 0

                if prev_total > 0:
                    trend_pct = ((current_total - prev_total) / prev_total) * 100
                    trend_arrow = "▲" if trend_pct > 0 else "▼" if trend_pct < 0 else "="
                    trend_color = "#2e7d32" if trend_pct > 0 else "#c62828" if trend_pct < 0 else "#757575"
                else:
                    trend_pct = 0
                    trend_arrow = "="
                    trend_color = "#757575"

                # Timeline and Scatter plot side by side
                col_timeline, col_scatter = st.columns(2)

                with col_timeline:
                    st.markdown("**📈 Línea de Tiempo de Reservas**")

                    # Create timeline plot
                    fig_timeline = go.Figure()

                    # Add current period line
                    fig_timeline.add_trace(go.Scatter(
                        x=activity_counts['time_bucket'],
                        y=activity_counts['total_activities'],
                        mode='lines+markers',
                        name='Período actual',
                        line=dict(color=US_OPEN_BLUE, width=2),
                        marker=dict(size=6),
                        hovertemplate='<b>%{x|' + time_format + '}</b><br>Reservas: %{y}<extra></extra>'
                    ))

                    # Add previous period comparison line (if data exists)
                    if prev_activity_counts is not None and len(prev_activity_counts) > 0:
                        fig_timeline.add_trace(go.Scatter(
                            x=prev_activity_counts['time_bucket_shifted'],
                            y=prev_activity_counts['total_activities'],
                            mode='lines',
                            name='Período anterior',
                            line=dict(color='#CCCCCC', width=2, dash='dash'),
                            hovertemplate='<b>Período anterior</b><br>Reservas: %{y}<extra></extra>'
                        ))

                    fig_timeline.update_layout(
                        height=400,
                        showlegend=True,
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                        margin=dict(l=0, r=0, t=40, b=0),
                        xaxis_title='Tiempo',
                        yaxis_title='Reservas',
                        xaxis=dict(tickformat='%Y-%m-%d %H:%M' if selected_granularity == 'hour' else time_format)
                    )

                    st.plotly_chart(fig_timeline, use_container_width=True)

                    # Trend indicator and peak info
                    col_trend, col_peak = st.columns(2)
                    with col_trend:
                        st.markdown(f"""
                        <div style="background: #f5f5f5; padding: 10px; border-radius: 8px; text-align: center;">
                            <span style="font-size: 1.5em; color: {trend_color}; font-weight: bold;">{trend_arrow} {abs(trend_pct):.1f}%</span>
                            <br><span style="color: #666; font-size: 0.85em;">vs período anterior</span>
                        </div>
                        """, unsafe_allow_html=True)
                    with col_peak:
                        peak_activity = activity_counts.loc[activity_counts['total_activities'].idxmax()]
                        days_spanish = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
                        peak_day_name = days_spanish[peak_activity['time_bucket'].weekday()]
                        st.markdown(f"""
                        <div style="background: #f5f5f5; padding: 10px; border-radius: 8px; text-align: center;">
                            <span style="font-size: 1.2em; font-weight: bold;">📊 Pico</span>
                            <br><span style="color: #666; font-size: 0.85em;">{peak_day_name} {peak_activity['time_bucket'].strftime(time_format)}</span>
                            <br><span style="font-weight: bold;">{int(peak_activity['total_activities'])} reservas</span>
                        </div>
                        """, unsafe_allow_html=True)

                with col_scatter:
                    st.markdown("**👥 Reservas por Usuario**")

                    # Prepare scatter plot data
                    df_scatter = pd.DataFrame(timeline_data)
                    # Timestamps are already in Colombian timezone, just parse them
                    df_scatter['created_at'] = pd.to_datetime(df_scatter['created_at'])
                    df_scatter['user_name'] = df_scatter['users'].apply(
                        lambda x: x.get('full_name', 'Desconocido') if isinstance(x, dict) else 'Desconocido'
                    )
                    df_scatter['user_email'] = df_scatter['users'].apply(
                        lambda x: x.get('email', '') if isinstance(x, dict) else ''
                    )

                    # Create scatter plot - showing users over time
                    fig_scatter = px.scatter(
                        df_scatter,
                        x='created_at',
                        y='user_name',
                        color='user_name',
                        hover_data={
                            'created_at': '|%Y-%m-%d %H:%M',
                            'user_name': False,
                            'user_email': True,
                            'activity_type': True
                        },
                        labels={
                            'created_at': 'Tiempo',
                            'user_name': 'Usuario'
                        }
                    )

                    fig_scatter.update_layout(
                        height=400,
                        showlegend=False,
                        margin=dict(l=0, r=0, t=20, b=0),
                        xaxis=dict(tickformat='%Y-%m-%d %H:%M')
                    )
                    fig_scatter.update_traces(marker=dict(size=8, opacity=0.7))

                    st.plotly_chart(fig_scatter, use_container_width=True)

                    # Show most active user
                    user_activity_count = df_scatter.groupby('user_name').size().reset_index(name='count')
                    if not user_activity_count.empty:
                        top_user = user_activity_count.loc[user_activity_count['count'].idxmax()]
                        st.info(f"🏆 **Más activo:** {top_user['user_name']} ({int(top_user['count'])} reservas)")

            else:
                st.info("ℹ️ No hay datos de reservas en el período seleccionado. La tabla debe existir y tener datos.")

        except Exception as e:
            st.warning(f"⚠️ Analytics no disponible: {str(e)}")

    st.divider()

    # Heatmap de uso por día y hora
    st.subheader("🔥 Mapa de Calor: Uso por Día y Hora")

    # Filter selector
    col_filter, col_spacer = st.columns([1, 3])
    with col_filter:
        heatmap_filter = st.selectbox(
            "Período",
            options=[("Últimos 30 días", 30), ("Últimos 90 días", 90), ("Todo el tiempo", None)],
            format_func=lambda x: x[0],
            index=0,
            key="heatmap_filter"
        )
        days_filter = heatmap_filter[1]

    # Get heatmap data
    heatmap_data = get_cached_heatmap_data(days_filter)

    if any(sum(row) > 0 for row in heatmap_data):
        # Create heatmap
        days_spanish = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        hours = [f"{h}:00" for h in range(6, 21)]

        fig_heatmap = go.Figure(data=go.Heatmap(
            z=heatmap_data,
            x=hours,
            y=days_spanish,
            colorscale=[
                [0, '#f5f5f5'],      # No reservations - light gray
                [0.25, '#c8e6c9'],   # Low - light green
                [0.5, '#81c784'],    # Medium - green
                [0.75, '#43a047'],   # High - darker green
                [1, '#1b5e20']       # Very high - dark green
            ],
            hovertemplate='<b>%{y}</b> a las <b>%{x}</b><br>%{z} reservas<extra></extra>',
            showscale=True,
            colorbar=dict(
                title=dict(text="Reservas", side="right")
            )
        ))

        fig_heatmap.update_layout(
            height=350,
            margin=dict(l=0, r=0, t=20, b=0),
            xaxis_title='Hora',
            yaxis_title='',
            yaxis=dict(autorange='reversed')  # Monday at top
        )

        st.plotly_chart(fig_heatmap, use_container_width=True)

        # Summary stats below heatmap
        # Find busiest and least busy day
        day_totals = [sum(row) for row in heatmap_data]
        busiest_day_idx = day_totals.index(max(day_totals))
        busiest_day = days_spanish[busiest_day_idx]
        least_busy_day_idx = day_totals.index(min(day_totals))
        least_busy_day = days_spanish[least_busy_day_idx]

        # Find busiest and least busy hour
        hour_totals = [sum(heatmap_data[d][h] for d in range(7)) for h in range(15)]
        busiest_hour_idx = hour_totals.index(max(hour_totals))
        busiest_hour = f"{busiest_hour_idx + 6}:00"
        least_busy_hour_idx = hour_totals.index(min(hour_totals))
        least_busy_hour = f"{least_busy_hour_idx + 6}:00"

        # Total reservations
        total_reservations = sum(day_totals)

        # Row 1: Busiest metrics
        col_busiest_day, col_busiest_hour, col_total = st.columns(3)

        with col_busiest_day:
            st.metric("📅 Día más ocupado", busiest_day, f"{day_totals[busiest_day_idx]} reservas")

        with col_busiest_hour:
            st.metric("⏰ Hora más popular", busiest_hour, f"{hour_totals[busiest_hour_idx]} reservas")

        with col_total:
            st.metric("🎾 Total reservas", total_reservations, heatmap_filter[0])

        # Row 2: Least busy metrics
        col_least_day, col_least_hour, col_spacer = st.columns(3)

        with col_least_day:
            st.metric("📅 Día menos ocupado", least_busy_day, f"{day_totals[least_busy_day_idx]} reservas")

        with col_least_hour:
            st.metric("⏰ Hora menos popular", least_busy_hour, f"{hour_totals[least_busy_hour_idx]} reservas")
    else:
        st.info("No hay datos de reservas disponibles para el período seleccionado")

    st.divider()

    # Tasa de Ocupación
    st.subheader("📊 Tasa de Ocupación")

    # Initialize session state for occupancy navigation
    if 'occupancy_scale' not in st.session_state:
        st.session_state.occupancy_scale = 'weekly'
    if 'occupancy_offset' not in st.session_state:
        st.session_state.occupancy_offset = 0

    # Scale selector and navigation
    col_scale, col_nav_prev, col_nav_current, col_nav_next = st.columns([2, 1, 1, 1])

    with col_scale:
        scale_options = {'Semanal': 'weekly', 'Mensual': 'monthly', 'Anual': 'yearly'}
        selected_scale_label = st.selectbox(
            "Escala",
            options=list(scale_options.keys()),
            index=list(scale_options.values()).index(st.session_state.occupancy_scale),
            key="occupancy_scale_select"
        )
        new_scale = scale_options[selected_scale_label]
        if new_scale != st.session_state.occupancy_scale:
            st.session_state.occupancy_scale = new_scale
            st.session_state.occupancy_offset = 0
            st.rerun()

    scale = st.session_state.occupancy_scale
    nav_label = {'weekly': 'Semana', 'monthly': 'Mes', 'yearly': 'Año'}[scale]

    with col_nav_prev:
        if st.button(f"⬅️ Anterior", key="occ_prev"):
            st.session_state.occupancy_offset -= 1
            st.rerun()

    with col_nav_current:
        if st.button(f"📍 {nav_label} Actual", key="occ_current"):
            st.session_state.occupancy_offset = 0
            st.rerun()

    with col_nav_next:
        if st.button(f"Siguiente ➡️", key="occ_next"):
            st.session_state.occupancy_offset += 1
            st.rerun()

    # Get occupancy data
    occupancy_data = get_cached_occupancy_data(scale, st.session_state.occupancy_offset)
    historic_avg = get_cached_historic_average_occupancy()

    if occupancy_data['dates']:
        # Period label
        st.markdown(f"**{occupancy_data['period_label']}**")

        # Average occupancy cards
        col_period_avg, col_historic_avg = st.columns(2)

        with col_period_avg:
            avg_occ = occupancy_data['average_occupancy']
            avg_color = '#2e7d32' if avg_occ >= 70 else '#f57c00' if avg_occ >= 40 else '#757575'
            period_name = {'weekly': 'esta semana', 'monthly': 'este mes', 'yearly': 'este año'}[scale]
            st.markdown(f"""
            <div style="background: #f5f5f5; padding: 20px; border-radius: 12px; text-align: center;">
                <span style="font-size: 2.5em; color: {avg_color}; font-weight: bold;">{avg_occ}%</span>
                <br><span style="color: #666;">Promedio {period_name}</span>
            </div>
            """, unsafe_allow_html=True)

        with col_historic_avg:
            hist_color = '#2e7d32' if historic_avg >= 70 else '#f57c00' if historic_avg >= 40 else '#757575'
            st.markdown(f"""
            <div style="background: #f5f5f5; padding: 20px; border-radius: 12px; text-align: center;">
                <span style="font-size: 2.5em; color: {hist_color}; font-weight: bold;">{historic_avg}%</span>
                <br><span style="color: #666;">Promedio histórico</span>
            </div>
            """, unsafe_allow_html=True)

        # Bar chart with occupancy rates
        current_idx = occupancy_data['current_index']

        # Create colors: past/current in blue, future in gray
        if st.session_state.occupancy_offset == 0 and current_idx >= 0:
            colors = [US_OPEN_BLUE if i <= current_idx else '#CCCCCC' for i in range(len(occupancy_data['dates']))]
        elif st.session_state.occupancy_offset < 0:
            colors = [US_OPEN_BLUE] * len(occupancy_data['dates'])  # All past
        else:
            colors = ['#CCCCCC'] * len(occupancy_data['dates'])  # All future

        fig_occupancy = go.Figure(data=[
            go.Bar(
                x=occupancy_data['dates'],
                y=occupancy_data['occupancy_rates'],
                marker_color=colors,
                text=[f"{rate}%" for rate in occupancy_data['occupancy_rates']],
                textposition='outside',
                hovertemplate='<b>%{x}</b><br>Ocupación: %{y}%<br>Reservas: %{customdata[0]}<br>Slots disponibles: %{customdata[1]}<extra></extra>',
                customdata=list(zip(occupancy_data['reservations'], occupancy_data['available_slots']))
            )
        ])

        fig_occupancy.update_layout(
            height=300,
            margin=dict(l=0, r=0, t=20, b=0),
            xaxis_title='',
            yaxis_title='Ocupación (%)',
            yaxis=dict(range=[0, 105]),
            showlegend=False
        )

        # Add period average reference line
        fig_occupancy.add_hline(
            y=avg_occ,
            line_dash="dash",
            line_color=avg_color,
            annotation_text=f"Promedio {avg_occ}%",
            annotation_position="right"
        )

        st.plotly_chart(fig_occupancy, use_container_width=True)

        # Details row with dynamic labels
        col1, col2, col3 = st.columns(3)

        # Calculate based on current data (up to current index if current period)
        if st.session_state.occupancy_offset == 0 and current_idx >= 0:
            valid_rates = occupancy_data['occupancy_rates'][:current_idx + 1]
            valid_reservations = occupancy_data['reservations'][:current_idx + 1]
            valid_slots = occupancy_data['available_slots'][:current_idx + 1]
        else:
            valid_rates = occupancy_data['occupancy_rates']
            valid_reservations = occupancy_data['reservations']
            valid_slots = occupancy_data['available_slots']

        if valid_rates:
            best_idx = valid_rates.index(max(valid_rates))
            best_label = occupancy_data['dates'][best_idx]

            with col1:
                label_prefix = {'weekly': '📅 Mejor día', 'monthly': '📅 Mejor semana', 'yearly': '📅 Mejor mes'}[scale]
                st.metric(label_prefix, best_label, f"{valid_rates[best_idx]}%")

            with col2:
                period_label = {'weekly': 'esta semana', 'monthly': 'este mes', 'yearly': 'este año'}[scale]
                st.metric(f"🎾 Reservas {period_label}", sum(valid_reservations))

            with col3:
                st.metric("📅 Slots usados", f"{sum(valid_reservations)}/{sum(valid_slots)}")
    else:
        st.info("No hay datos de ocupación disponibles")

    st.divider()

    # Estadísticas de usuarios
    st.subheader("🏆 Usuarios Más Activos")
    user_stats = get_cached_user_reservation_statistics()
    if user_stats:
        for i, user in enumerate(user_stats[:5], 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            expander_title = f"{medal} **{user['name']}** • {user['reservations']} reservas"

            with st.expander(expander_title, expanded=False):
                user_detail, error = admin_db_manager.search_users_detailed(user['email'])
                if error:
                    st.error(f"❌ {error}")
                elif user_detail:
                    user_info = user_detail[0]
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**📧 Email:** {user_info['email']}")
                        st.markdown(f"**🎯 Estado:** {'✅ Activo' if user_info['is_active'] else '❌ Inactivo'}")
                        st.markdown(f"**💰 Créditos Usados:** {user['reservations']}")
                    with col2:
                        st.markdown(f"**⭐ Tipo:** {'Del Comité' if user_info.get('is_vip', False) else 'Regular'}")
                        st.markdown(f"**📅 Día Favorito:** {user.get('favorite_day', 'N/A')}")
                        st.markdown(f"**🕐 Hora Favorita:** {user.get('favorite_hour', 'N/A')}")
                else:
                    st.warning("⚠️ No se pudieron cargar los detalles del usuario")
    else:
        st.info("📊 No hay datos de usuarios disponibles")

    st.divider()

    # NUEVA SECCIÓN: Vista de Calendario Semanal
    st.subheader("📅 Calendario de Reservas Semanal")

    # Controles de navegación
    col1, col2, col3, col4 = st.columns([1, 1, 2, 1])

    # Inicializar week_offset si no existe
    if 'calendar_week_offset' not in st.session_state:
        st.session_state.calendar_week_offset = 0

    with col1:
        if st.button("⬅️ Anterior", key="prev_week"):
            st.session_state.calendar_week_offset -= 1
            st.rerun()

    with col2:
        if st.button("➡️ Siguiente", key="next_week"):
            st.session_state.calendar_week_offset += 1
            st.rerun()

    with col3:
        if st.button("📍 Semana Actual", key="current_week"):
            st.session_state.calendar_week_offset = 0
            st.rerun()

    with col4:
        if st.button("🔄 Actualizar", key="refresh_calendar"):
            st.cache_data.clear()
            st.success("✅ Calendario actualizado")

    # Obtener datos del calendario
    calendar_data = get_cached_weekly_calendar_data(st.session_state.calendar_week_offset)

    if calendar_data['week_dates']:
        # Mostrar información de la semana
        week_info = f"📊 Semana del {calendar_data['week_start']} al {calendar_data['week_end']} • {calendar_data['total_reservations']} reservas"
        st.info(week_info)

        # Crear el calendario como tabla
        week_dates = calendar_data['week_dates']
        reservations_grid = calendar_data['reservations_grid']
        maintenance_grid = calendar_data.get('maintenance_grid', {})

        # Nombres de los días
        day_names = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']

        # Horarios de la cancha (6 AM a 8 PM)
        court_hours = list(range(6, 21))

        # Crear DataFrame para el calendario
        # Preparar datos para la tabla
        calendar_table = []

        for hour in court_hours:
            row = {'Hora': f"{hour:02d}:00"}

            for i, date in enumerate(week_dates):
                date_str = date.strftime('%Y-%m-%d')
                day_name = day_names[i]

                # Check for maintenance first (it blocks reservations)
                maintenance = maintenance_grid.get(date_str, {}).get(hour)
                reservation = reservations_grid.get(date_str, {}).get(hour)

                if maintenance:
                    # Check if it's Tennis School or regular maintenance
                    if maintenance.get('type') == 'tennis_school':
                        row[f"{day_name}\n{date.strftime('%d/%m')}"] = "🎾🏫 Escuela de Tenis"
                    else:
                        row[f"{day_name}\n{date.strftime('%d/%m')}"] = f"🔧 {maintenance.get('reason', 'Mantenimiento')}"
                elif reservation:
                    # Mostrar nombre completo del usuario
                    name = reservation['name']
                    row[f"{day_name}\n{date.strftime('%d/%m')}"] = f"🎾 {name}"
                else:
                    row[f"{day_name}\n{date.strftime('%d/%m')}"] = "⚪ Libre"

            calendar_table.append(row)

        # Crear DataFrame
        df_calendar = pd.DataFrame(calendar_table)

        # Mostrar la tabla con estilo
        st.markdown("### 📋 Vista de Calendario")

        # Aplicar estilos a la tabla
        def style_calendar_table(val):
            """Aplicar estilos según el contenido"""
            val_str = str(val)

            # Tennis School slots - Light green background, dark green border and text
            if "🎾🏫" in val_str or "Escuela de Tenis" in val_str:
                return 'background-color: #d4edda; color: #155724; text-align: center; font-weight: bold; border: 2px solid #28a745; font-size: 0.9em;'
            # Regular maintenance - Gray/orange
            elif "🔧" in val_str:
                return 'background-color: #fff3cd; color: #856404; text-align: center; font-weight: bold; border: 1px solid #ffc107;'
            # Regular reservations - Light green
            elif "🎾" in val_str and "🏫" not in val_str:
                return 'background-color: #e8f5e8; color: #2e7d32; text-align: center; font-weight: bold; border: 1px solid #4caf50;'
            # Free slots
            elif "⚪ Libre" in val_str:
                return 'background-color: #f5f5f5; color: #757575; text-align: center; border: 1px solid #e0e0e0;'
            # Hour column
            elif "Hora" in val_str:
                return 'background-color: #1976d2; color: white; text-align: center; font-weight: bold; border: 1px solid #1565c0;'
            # Day headers
            else:
                return 'text-align: center; font-weight: bold; border: 1px solid #2478CC; background-color: #e3f2fd;'

        # Mostrar tabla estilizada
        styled_df = df_calendar.style.map(style_calendar_table)
        st.dataframe(styled_df, use_container_width=True, hide_index=True)

        # Leyenda
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown("🎾 **Reservado**")
        with col2:
            st.markdown("🎾🏫 **Escuela de Tenis**")
        with col3:
            st.markdown("🔧 **Mantenimiento**")
        with col4:
            st.markdown("⚪ **Libre**")

    else:
        st.error("❌ Error cargando datos del calendario")

    st.divider()

    # Alertas y Anomalías
    st.subheader("🚨 Alertas y Anomalías")

    alerts = get_cached_alerts_and_anomalies()

    for alert in alerts:
        alert_type = alert['type']
        if alert_type == 'warning':
            st.warning(f"{alert['icon']} **{alert['title']}**: {alert['message']}")
        elif alert_type == 'error':
            st.error(f"{alert['icon']} **{alert['title']}**: {alert['message']}")
        elif alert_type == 'success':
            st.success(f"{alert['icon']} **{alert['title']}**: {alert['message']}")
        else:  # info
            st.info(f"{alert['icon']} **{alert['title']}**: {alert['message']}")

def show_reservations_management_tab():
    """Gestión de reservas por usuario"""

    # Tasa de Cancelación
    st.subheader("❌ Tasa de Cancelación")

    # Period selector
    col_period, col_spacer = st.columns([1, 3])
    with col_period:
        cancel_period = st.selectbox(
            "Período",
            options=[("Últimos 30 días", 30), ("Últimos 60 días", 60), ("Últimos 90 días", 90)],
            format_func=lambda x: x[0],
            index=0,
            key="cancellation_period"
        )
        cancel_days = cancel_period[1]

    cancel_stats = get_cached_cancellation_statistics(cancel_days)

    # Card style for consistent sizing
    card_style = "background: #f5f5f5; padding: 15px; border-radius: 12px; text-align: center; min-height: 85px; display: flex; flex-direction: column; justify-content: center;"

    # Main metrics row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        rate = cancel_stats['cancellation_rate']
        rate_color = '#2e7d32' if rate <= 5 else '#f57c00' if rate <= 15 else '#c62828'
        st.markdown(f"""
        <div style="{card_style}">
            <span style="font-size: 2em; color: {rate_color}; font-weight: bold;">{rate}%</span>
            <span style="color: #666; font-size: 0.85em;">Tasa de cancelación</span>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div style="{card_style}">
            <span style="font-size: 2em; font-weight: bold;">{cancel_stats['total_cancellations']}</span>
            <span style="color: #666; font-size: 0.85em;">Cancelaciones</span>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div style="{card_style}">
            <span style="font-size: 1.1em; font-weight: bold;">📝 {cancel_stats['main_reason']}</span>
            <span style="color: #666; font-size: 0.85em;">Motivo principal ({cancel_stats['main_reason_pct']}%)</span>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div style="{card_style}">
            <span style="font-size: 1.1em; font-weight: bold;">👤 {cancel_stats['top_user_name']}</span>
            <span style="color: #666; font-size: 0.85em;">Más cancelaciones ({cancel_stats['top_user_count']})</span>
        </div>
        """, unsafe_allow_html=True)

    # Summary info
    st.caption(f"📊 De {cancel_stats['total_reservations']} reservas realizadas, {cancel_stats['total_cancellations']} fueron canceladas en los últimos {cancel_days} días.")

    st.divider()

    # Gestión de Reservas por Usuario
    st.subheader("📅 Gestión de Reservas por Usuario")

    # Buscador de usuario
    col1, col2 = st.columns([3, 1])

    with col1:
        search_term = st.text_input(
            "🔍 Buscar usuario por nombre o email:",
            placeholder="Ingresa nombre o email del usuario",
            key="search_reservations_user"
        )

    with col2:
        search_button = st.button("🔍 Buscar", type="primary")

    if search_term and search_button:
        # Buscar usuarios que coincidan
        matching_users, error = admin_db_manager.search_users_for_reservations(search_term)

        if error:
            # Mostrar error de base de datos
            st.error(f"❌ {error}")
            st.session_state.matching_users_list = None
        elif matching_users:
            if len(matching_users) == 1:
                st.session_state.selected_user_for_reservations = matching_users[0]
                st.session_state.matching_users_list = None  # Limpiar lista
            else:
                # Múltiples usuarios encontrados - guardar en session_state
                st.session_state.matching_users_list = matching_users
                # Limpiar selección anterior
                if 'selected_user_for_reservations' in st.session_state:
                    del st.session_state.selected_user_for_reservations
        else:
            st.warning("No se encontraron usuarios con ese criterio")
            st.session_state.matching_users_list = None

    # Mostrar lista de usuarios encontrados si hay múltiples
    if st.session_state.get('matching_users_list'):
        st.write("**Usuarios encontrados:**")
        for user in st.session_state.matching_users_list:
            # Usar email como parte de la key para hacer cada botón único
            button_key = f"select_user_{user['email'].replace('@', '_').replace('.', '_')}"
            if st.button(f"{user['name']} ({user['email']})", key=button_key):
                st.session_state.selected_user_for_reservations = user
                st.session_state.matching_users_list = None  # Limpiar lista después de seleccionar
                st.rerun()

    # Mostrar reservas del usuario seleccionado
    if 'selected_user_for_reservations' in st.session_state:
        user = st.session_state.selected_user_for_reservations

        st.markdown(f"### 📋 Reservas de {user['name']}")
        st.info(f"**Email:** {user['email']}")

        # Filtros de reservas
        col1, col2 = st.columns([2, 2])

        with col1:
            filter_type = st.selectbox(
                "📅 Filtrar reservas:",
                options=['upcoming', 'all', 'past', 'this_week', 'this_month'],
                format_func=lambda x: {
                    'all': 'Todas las reservas',
                    'upcoming': 'Próximas (hoy y futuro)',
                    'past': 'Pasadas',
                    'this_week': 'Esta semana',
                    'this_month': 'Este mes'
                }[x],
                index=0,  # Default: upcoming (most recent first)
                key='reservation_filter'
            )

        # Obtener reservas del usuario con filtro
        user_reservations = admin_db_manager.get_user_reservations_history(user['email'], filter_type)

        if not user_reservations:
            st.warning("No hay reservas para el filtro seleccionado")
        else:
            # Group reservations by date
            reservations_by_date = defaultdict(list)
            for reservation in user_reservations:
                reservations_by_date[reservation['date']].append(reservation)

            # Display grouped reservations
            for date, reservations in reservations_by_date.items():
                fecha_display = format_date_display(date)

                # Create collapsible section for each date
                with st.expander(f"📅 {fecha_display} ({len(reservations)} reserva{'s' if len(reservations) > 1 else ''})", expanded=True):
                    for i, reservation in enumerate(reservations):
                        # Display reservation with cancel option
                        col1, col2 = st.columns([2, 1])

                        with col1:
                            st.markdown(f"""
                            **🕐 Hora:** {reservation['hour']}:00 - {reservation['hour'] + 1}:00
                            **📝 Creada:** {reservation['created_at'][:10]}
                            """)

                        with col2:
                            # Formulario para cancelación con motivo
                            with st.form(f"cancel_form_{reservation['id']}", clear_on_submit=True):
                                cancellation_reason = st.text_input(
                                    "Motivo (opcional):",
                                    placeholder="Ej: Lluvia",
                                    max_chars=100,
                                    key=f"reason_{reservation['id']}"
                                )

                                cancel_submitted = st.form_submit_button(
                                    "❌ Cancelar",
                                    type="secondary",
                                    use_container_width=True
                                )

                                if cancel_submitted:
                                    admin_user = st.session_state.get('admin_user', {})
                                    admin_username = admin_user.get('username')

                                    # Validar que tenemos el username del admin
                                    if not admin_username:
                                        st.error("❌ Error: No se pudo identificar al usuario administrador. Por favor, vuelve a iniciar sesión.")
                                    else:
                                        with st.spinner("🔄 Cancelando reserva..."):
                                            success = admin_db_manager.cancel_reservation_with_notification(
                                                reservation['id'],
                                                user['email'],
                                                cancellation_reason.strip() if cancellation_reason else "",
                                                admin_username
                                            )

                                            if success:
                                                st.success("✅ Reserva cancelada exitosamente y usuario notificado")
                                                # Mantener usuario seleccionado para ver reservas actualizadas
                                                # (No eliminamos selected_user_for_reservations)

                                                time.sleep(1.5)
                                                st.rerun()
                                            else:
                                                st.error("❌ Error al cancelar reserva. No se completaron todas las operaciones requeridas.")

                        # Add separator between reservations
                        if i < len(reservations) - 1:
                            st.markdown("---")

    st.divider()

    # NUEVA SECCIÓN: Historial de Cancelaciones
    st.subheader("📋 Historial de Cancelaciones")

    # Controles para el historial
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        days_back = st.selectbox(
            "Mostrar cancelaciones de:",
            options=[7, 15, 30, 60, 90],
            index=2,  # Default: 30 días
            format_func=lambda x: f"Últimos {x} días",
            key="cancellation_days_selector"
        )

    with col2:
        if st.button("🔄 Actualizar Historial", key="refresh_cancellations"):
            st.cache_data.clear()
            st.success("✅ Historial actualizado")

    with col3:
        show_all_cancellations = st.checkbox("Ver todas", key="show_all_cancellations")

    # Obtener historial de cancelaciones
    cancellations = admin_db_manager.get_cancellation_history(
        days_back if not show_all_cancellations else None
    )

    if cancellations:
        st.info(
            f"📊 **Total de cancelaciones:** {len(cancellations)} {'en todos los registros' if show_all_cancellations else f'en los últimos {days_back} días'}")

        # Convertir a DataFrame para mejor visualización
        df_cancellations = pd.DataFrame(cancellations)

        # Renombrar columnas para display
        display_df = df_cancellations.rename(columns={
            'user_name': 'Usuario',
            'user_email': 'Email',
            'reservation_date': 'Fecha Reserva',
            'reservation_hour': 'Hora',
            'cancellation_reason': 'Motivo',
            'cancelled_by': 'Cancelado Por',
            'cancelled_at': 'Fecha Cancelación',
            'credits_refunded': 'Créditos Reembolsados'
        })

        # Seleccionar columnas a mostrar
        columns_to_show = [
            'Usuario', 'Email', 'Fecha Reserva', 'Hora', 'Motivo',
            'Cancelado Por', 'Fecha Cancelación', 'Créditos Reembolsados'
        ]

        # Mostrar tabla interactiva
        st.dataframe(
            display_df[columns_to_show],
            use_container_width=True,
            hide_index=True,
            column_config={
                "Hora": st.column_config.TextColumn(
                    "Hora",
                    help="Hora de la reserva original",
                    width="small"
                ),
                "Motivo": st.column_config.TextColumn(
                    "Motivo",
                    help="Motivo de la cancelación",
                    width="medium"
                ),
                "Fecha Cancelación": st.column_config.DatetimeColumn(
                    "Fecha Cancelación",
                    help="Cuándo se canceló la reserva",
                    width="medium"
                ),
                "Créditos Reembolsados": st.column_config.NumberColumn(
                    "Créditos",
                    help="Créditos reembolsados",
                    width="small"
                )
            }
        )

def show_user_detailed_info(user):
    """Mostrar información detallada del usuario con feedback mejorado"""
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"""
        **📊 Información General:**
        - **Nombre:** {user['full_name']}
        - **Email:** {user['email']}
        - **Créditos:** {user['credits'] or 0}
        - **Estado:** {'✅ Activo' if user.get('is_active', True) else '🚫 Bloqueado'}
        - **Pertenece al Comité:** {'⭐ Sí' if user.get('is_vip', False) else '👤 No'}
        - **Primer login completado:** {'✅ Sí' if user.get('first_login_completed', False) else '⏳ Pendiente'}
        - **Registrado:** {user['created_at'][:10] if 'created_at' in user and user['created_at'] else 'N/A'}
        """)

    with col2:
        # Obtener estadísticas del usuario
        stats = admin_db_manager.get_user_stats(user['id'])
        st.markdown(f"""
        **📈 Estadísticas:**
        - **Total reservas:** {stats['total_reservations']}
        - **Reservas activas:** {stats['active_reservations']}
        - **Última reserva:** {stats['last_reservation'] or 'Nunca'}
        """)

    # Edit name section
    edit_key = f"edit_mode_{user['id']}"
    if edit_key not in st.session_state:
        st.session_state[edit_key] = False

    if st.session_state[edit_key]:
        # Edit mode
        col_input, col_save, col_cancel = st.columns([3, 1, 1])
        with col_input:
            new_name = st.text_input(
                "Nuevo nombre:",
                value=user['full_name'],
                key=f"new_name_{user['id']}",
                label_visibility="collapsed"
            )
        with col_save:
            if st.button("💾 Guardar", key=f"save_name_{user['id']}"):
                if new_name and new_name.strip():
                    success, message = admin_db_manager.update_user_name(user['id'], new_name.strip())
                    if success:
                        st.success(message)
                        st.session_state[edit_key] = False
                        st.session_state.found_users = []
                        get_cached_search_users.clear()
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    st.warning("El nombre no puede estar vacío")
        with col_cancel:
            if st.button("❌ Cancelar", key=f"cancel_edit_{user['id']}"):
                st.session_state[edit_key] = False
                st.rerun()
    else:
        # Action buttons row
        is_active = user.get('is_active', True)
        block_text = "🚫 Bloquear Usuario" if is_active else "✅ Desbloquear Usuario"
        block_type = "secondary" if is_active else "primary"

        col_edit, col_block = st.columns(2)

        with col_edit:
            if st.button("✏️ Editar Nombre", key=f"edit_btn_{user['id']}", type="secondary", use_container_width=True):
                st.session_state[edit_key] = True
                st.rerun()

        with col_block:
            if st.button(block_text, key=f"toggle_block_{user['id']}", type=block_type, use_container_width=True):
                admin_user = st.session_state.get('admin_user', {})
                admin_username = admin_user.get('username', 'admin')

                with st.spinner(f"🔄 {'Bloqueando' if is_active else 'Desbloqueando'} usuario..."):
                    if is_active:
                        success, message = admin_db_manager.block_user(user['email'], admin_username)
                        new_state = "🚫 Bloqueado"
                    else:
                        success, message = admin_db_manager.unblock_user(user['email'], admin_username)
                        new_state = "✅ Activo"

                    if success:
                        st.session_state.found_users = []
                        st.success(f"{message}\n\n**Nuevo estado del usuario:** {new_state}")
                        st.rerun()
                    else:
                        st.error(message)


def show_users_management_tab():
    """Gestión mejorada de usuarios con vista de base de datos siempre visible"""

    # Obtener estadísticas (cached)
    stats = get_cached_system_statistics()

    # Métricas principales - Usuarios
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{stats['total_users']}</div>
            <div class="stat-label">Usuarios Registrados</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{stats['active_users_30d']}</div>
            <div class="stat-label">Usuarios Activos (30 días)</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{stats['vip_users']}</div>
            <div class="stat-label">Usuarios del Comité</div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    st.subheader("👥 Gestión de Usuarios")

    # Buscador en la parte superior
    col1, col2 = st.columns([3, 1])

    with col1:
        search_user = st.text_input("🔍 Buscar usuario por nombre o email:",
                                    placeholder="Ingresa nombre o email del usuario",
                                    key="search_users")

    with col2:
        if st.button("🔍 Buscar Usuario", type="primary"):
            if search_user:
                with st.spinner("Buscando..."):
                    found_users, error = get_cached_search_users(search_user)
                if error:
                    st.error(f"❌ {error}")
                    st.session_state.found_users = []
                elif found_users:
                    st.session_state.found_users = found_users
                else:
                    st.warning("No se encontraron usuarios")
                    st.session_state.found_users = []

    # Mostrar usuarios encontrados (si hay búsqueda)
    if 'found_users' in st.session_state and st.session_state.found_users:
        st.markdown("### 🔍 Resultados de Búsqueda")

        for user in st.session_state.found_users:
            with st.expander(f"👤 {user['full_name']} ({user['email']})", expanded=False):
                show_user_detailed_info(user)

    st.divider()

    st.markdown("<br>", unsafe_allow_html=True)

    # Retención de Usuarios
    st.markdown("### 📊 Retención de Usuarios")

    retention_data = get_cached_user_retention_data()

    # Metrics row
    col1, col2, col3, col4 = st.columns(4)

    card_style = "background: #f5f5f5; padding: 15px; border-radius: 12px; text-align: center; min-height: 90px; display: flex; flex-direction: column; justify-content: center;"

    with col1:
        st.markdown(f"""
        <div style="{card_style}">
            <span style="font-size: 1.8em; color: #2e7d32; font-weight: bold;">{retention_data['new_users_this_month']}</span>
            <span style="color: #666; font-size: 0.85em;">Usuarios Nuevos (Este Mes)</span>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div style="{card_style}">
            <span style="font-size: 1.8em; color: #1565c0; font-weight: bold;">{retention_data['returning_users']}</span>
            <span style="color: #666; font-size: 0.85em;">Usuarios Recurrentes</span>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        retention_color = '#2e7d32' if retention_data['retention_rate'] >= 50 else '#f57c00' if retention_data['retention_rate'] >= 25 else '#c62828'
        st.markdown(f"""
        <div style="{card_style}">
            <span style="font-size: 1.8em; color: {retention_color}; font-weight: bold;">{retention_data['retention_rate']}%</span>
            <span style="color: #666; font-size: 0.85em;">Tasa de Retención</span>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div style="{card_style}">
            <span style="font-size: 1.8em; color: #6a1b9a; font-weight: bold;">{retention_data['avg_reservations_per_user']}</span>
            <span style="color: #666; font-size: 0.85em;">Promedio Reservas/Usuario</span>
        </div>
        """, unsafe_allow_html=True)

    # Frequency distribution chart
    st.markdown("**📊 Distribución por Frecuencia de Uso**")

    freq_data = retention_data['frequency_distribution']
    fig_freq = go.Figure(data=[
        go.Bar(
            x=['1 reserva', '2-5 reservas', '6-10 reservas', '10+ reservas'],
            y=[freq_data['1'], freq_data['2-5'], freq_data['6-10'], freq_data['10+']],
            marker_color=['#ffcdd2', '#fff9c4', '#c8e6c9', '#1b5e20'],
            text=[freq_data['1'], freq_data['2-5'], freq_data['6-10'], freq_data['10+']],
            textposition='auto'
        )
    ])

    fig_freq.update_layout(
        height=250,
        margin=dict(l=0, r=0, t=20, b=0),
        xaxis_title='',
        yaxis_title='Usuarios',
        showlegend=False
    )

    st.plotly_chart(fig_freq, use_container_width=True)

    st.divider()

    # Base de datos completa con paginación
    st.markdown("### 📊 Base de Usuarios Registrados")

    # Pagination settings
    USERS_PER_PAGE = 10

    # Initialize pagination state
    if 'users_page' not in st.session_state:
        st.session_state.users_page = 0

    # Get total count and calculate pages
    total_users = get_cached_users_count()
    total_pages = max(1, (total_users + USERS_PER_PAGE - 1) // USERS_PER_PAGE)

    # Ensure current page is valid
    if st.session_state.users_page >= total_pages:
        st.session_state.users_page = total_pages - 1
    if st.session_state.users_page < 0:
        st.session_state.users_page = 0

    current_page = st.session_state.users_page
    offset = current_page * USERS_PER_PAGE

    # Get users for current page
    with st.spinner("Cargando datos de usuarios..."):
        users_stats = get_cached_users_detailed_statistics(limit=USERS_PER_PAGE, offset=offset)

    if users_stats:
        df = pd.DataFrame(users_stats)
        df = df.rename(columns={
            'name': 'Nombre',
            'email': 'Email',
            'registered_date': 'Fecha Registro',
            'total_credits_bought': 'Créditos Comprados',
            'total_reservations': 'Reservas Totales',
            'favorite_day': 'Día Favorito',
            'favorite_time': 'Hora Favorita'
        })

        # Display with filters
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Email": st.column_config.TextColumn("Email", width="medium"),
                "Nombre": st.column_config.TextColumn("Nombre", width="medium"),
                "Créditos Comprados": st.column_config.NumberColumn("Créditos Comprados", format="%d 💰"),
                "Reservas Totales": st.column_config.NumberColumn("Reservas Totales", format="%d 🎾"),
            }
        )

        # Pagination controls
        col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])

        with col1:
            if st.button("⏮️ Primera", disabled=(current_page == 0), key="users_first"):
                st.session_state.users_page = 0
                st.rerun()

        with col2:
            if st.button("◀️ Anterior", disabled=(current_page == 0), key="users_prev"):
                st.session_state.users_page -= 1
                st.rerun()

        with col3:
            st.markdown(f"<div style='text-align: center; padding: 8px;'>Página **{current_page + 1}** de **{total_pages}** ({total_users} usuarios)</div>", unsafe_allow_html=True)

        with col4:
            if st.button("Siguiente ▶️", disabled=(current_page >= total_pages - 1), key="users_next"):
                st.session_state.users_page += 1
                st.rerun()

        with col5:
            if st.button("Última ⏭️", disabled=(current_page >= total_pages - 1), key="users_last"):
                st.session_state.users_page = total_pages - 1
                st.rerun()
    else:
        st.info("No hay usuarios registrados")

def show_credits_management_tab():
    # Estadísticas de créditos (usando stats del sistema)
    stats = get_cached_system_statistics()
    credit_stats = get_cached_credit_statistics()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{stats['total_credits_issued']}</div>
            <div class="stat-label">Créditos Totales Emitidos</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{stats['total_credits_balance']}</div>
            <div class="stat-label">Créditos en Sistema</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{credit_stats['users_with_credits']}</div>
            <div class="stat-label">Usuarios con Créditos</div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # Gestión de Créditos de Usuario
    st.subheader("💰 Gestionar Créditos de Usuario")

    # Inicializar session states si no existen
    if 'selected_user_for_credits' not in st.session_state:
        st.session_state.selected_user_for_credits = None
    if 'matching_users_credits' not in st.session_state:
        st.session_state.matching_users_credits = []

    # Buscador de usuario
    col1, col2 = st.columns([3, 1])

    with col1:
        search_term = st.text_input(
            "🔍 Buscar usuario por nombre o email:",
            placeholder="Ingresa nombre o email del usuario",
            key="search_credits_user"
        )

    with col2:
        if st.button("🔍 Buscar", type="primary", key="search_credits_btn"):
            if search_term:
                # Buscar usuarios que coincidan
                matching_users = admin_db_manager.search_users_for_credits(search_term)

                if matching_users:
                    if len(matching_users) == 1:
                        # Solo un usuario encontrado - seleccionar automáticamente
                        st.session_state.selected_user_for_credits = matching_users[0]
                        st.session_state.matching_users_credits = []
                        st.success(f"✅ Usuario seleccionado: {matching_users[0]['name']}")
                    else:
                        # Múltiples usuarios - guardar para mostrar
                        st.session_state.matching_users_credits = matching_users
                        st.session_state.selected_user_for_credits = None
                else:
                    st.warning("No se encontraron usuarios con ese criterio")
                    st.session_state.matching_users_credits = []
                    st.session_state.selected_user_for_credits = None

    # Mostrar lista de usuarios encontrados si hay múltiples
    if st.session_state.matching_users_credits:
        st.write("**Usuarios encontrados:**")

        for i, user in enumerate(st.session_state.matching_users_credits):
            with st.container():
                col_user, col_info, col_select = st.columns([2, 2, 1])

                with col_user:
                    st.write(f"**{user['name']}**")

                with col_info:
                    st.write(f"📧 {user['email']}")
                    st.write(f"🪙 {user['credits']} créditos")

                with col_select:
                    # Usar un key único y manejar la selección directamente
                    select_key = f"select_credit_user_{user['id']}_{i}"
                    if st.button("✅ Seleccionar", key=select_key):
                        st.session_state.selected_user_for_credits = user
                        st.session_state.matching_users_credits = []
                        st.rerun()

    # Mostrar usuario seleccionado y formulario de créditos
    selected_user = st.session_state.selected_user_for_credits

    if selected_user:
        # Mostrar información del usuario seleccionado
        st.markdown("### 👤 Usuario Seleccionado")

        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            st.info(f"**Nombre:** {selected_user['name']}")
        with col2:
            st.info(f"**Email:** {selected_user['email']}")
        with col3:
            st.info(f"**Créditos:** {selected_user['credits']}")

        # Formulario para gestionar créditos
        with st.form("manage_credits_form", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)

            with col1:
                operation = st.selectbox("Operación:", ["Agregar", "Quitar"])

            with col2:
                credits_amount = st.number_input("Cantidad:", min_value=1, max_value=100, value=1)

            with col3:
                reason = st.text_input("Motivo:", placeholder="Ej: Nueva Tiquetera")

            col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
            with col_btn2:
                submit_credits = st.form_submit_button(
                    f"💰 Confirmar",
                    type="primary",
                    use_container_width=True
                )

            if submit_credits:
                admin_user = st.session_state.get('admin_user', {})

                if operation == "Agregar":
                    success = admin_db_manager.add_credits_to_user(
                        selected_user['email'], credits_amount,
                        reason or "Créditos agregados por administrador",
                        admin_user.get('username', 'admin')
                    )
                    action_msg = f"agregados a"
                else:
                    success = admin_db_manager.remove_credits_from_user(
                        selected_user['email'], credits_amount,
                        reason or "Créditos removidos por administrador",
                        admin_user.get('username', 'admin')
                    )
                    action_msg = f"removidos de"

                if success:
                    st.success(f"✅ {credits_amount} créditos {action_msg} {selected_user['name']}")
                    email_manager.send_credits_notification(
                        selected_user['email'], credits_amount, reason, operation.lower()
                    )

                    # Limpiar selección después del éxito
                    st.session_state.selected_user_for_credits = None
                    st.session_state.matching_users_credits = []

                    # Pequeña pausa para mostrar el mensaje
                    import time
                    time.sleep(2)
                    st.rerun()
                else:
                    error_msg = "créditos insuficientes" if operation == "Quitar" else "error en la base de datos"
                    st.error(f"❌ Error: {error_msg}")

        # Botón para limpiar selección
        if st.button("🔄 Buscar Otro Usuario", type="secondary", key="clear_selection_credits"):
            st.session_state.selected_user_for_credits = None
            st.session_state.matching_users_credits = []
            st.rerun()

    else:
        # Mostrar instrucciones cuando no hay usuario seleccionado
        st.info("💡 Usa el buscador para encontrar y seleccionar un usuario")

    st.divider()

    # Economía de Créditos
    st.subheader("📈 Economía de Créditos")

    # Period selector
    col_period, col_spacer = st.columns([1, 3])
    with col_period:
        economy_period = st.selectbox(
            "Período",
            options=[("Últimos 30 días", 30), ("Últimos 60 días", 60), ("Últimos 90 días", 90)],
            format_func=lambda x: x[0],
            index=0,
            key="credit_economy_period"
        )
        economy_days = economy_period[1]

    economy_data = get_cached_credit_economy_data(economy_days)

    # Metrics cards
    col1, col2, col3, col4, col5 = st.columns(5)

    card_style = "background: #f5f5f5; padding: 15px; border-radius: 12px; text-align: center; min-height: 80px; display: flex; flex-direction: column; justify-content: center;"

    with col1:
        st.markdown(f"""
        <div style="{card_style}">
            <span style="font-size: 1.8em; color: #2e7d32; font-weight: bold;">+{economy_data['credits_granted']}</span>
            <span style="color: #666; font-size: 0.85em;">Otorgados</span>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div style="{card_style}">
            <span style="font-size: 1.8em; color: #c62828; font-weight: bold;">-{economy_data['credits_used']}</span>
            <span style="color: #666; font-size: 0.85em;">Usados</span>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div style="{card_style}">
            <span style="font-size: 1.8em; color: #1565c0; font-weight: bold;">+{economy_data['credits_refunded']}</span>
            <span style="color: #666; font-size: 0.85em;">Reembolsados</span>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div style="{card_style}">
            <span style="font-size: 1.8em; color: #6a1b9a; font-weight: bold;">-{economy_data['credits_removed']}</span>
            <span style="color: #666; font-size: 0.85em;">Removidos</span>
        </div>
        """, unsafe_allow_html=True)

    with col5:
        net = economy_data['net_flow']
        net_color = '#2e7d32' if net >= 0 else '#c62828'
        net_sign = '+' if net >= 0 else ''
        st.markdown(f"""
        <div style="{card_style}">
            <span style="font-size: 1.8em; color: {net_color}; font-weight: bold;">{net_sign}{net}</span>
            <span style="color: #666; font-size: 0.85em;">Balance Neto</span>
        </div>
        """, unsafe_allow_html=True)

    # Timeline chart
    if economy_data['timeline']['dates']:
        st.markdown("**📊 Flujo de Créditos**")

        fig_credits = go.Figure()

        # Add granted line
        fig_credits.add_trace(go.Scatter(
            x=economy_data['timeline']['dates'],
            y=economy_data['timeline']['granted'],
            mode='lines+markers',
            name='Otorgados',
            line=dict(color='#2e7d32', width=2),
            marker=dict(size=6)
        ))

        # Add used line
        fig_credits.add_trace(go.Scatter(
            x=economy_data['timeline']['dates'],
            y=economy_data['timeline']['used'],
            mode='lines+markers',
            name='Usados',
            line=dict(color='#c62828', width=2),
            marker=dict(size=6)
        ))

        # Add cumulative line
        fig_credits.add_trace(go.Scatter(
            x=economy_data['timeline']['dates'],
            y=economy_data['timeline']['cumulative'],
            mode='lines',
            name='Balance Acumulado',
            line=dict(color='#1565c0', width=2, dash='dash'),
            yaxis='y2'
        ))

        fig_credits.update_layout(
            height=350,
            margin=dict(l=0, r=0, t=30, b=0),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            xaxis_title='',
            yaxis_title='Créditos/día',
            yaxis2=dict(
                title='Balance Acumulado',
                overlaying='y',
                side='right'
            ),
            hovermode='x unified'
        )

        st.plotly_chart(fig_credits, use_container_width=True)
    else:
        st.info("No hay datos de transacciones en el período seleccionado")

    st.divider()

    # Historial de transacciones con paginación
    st.subheader("📋 Historial de Transacciones")

    # Pagination settings
    TRANSACTIONS_PER_PAGE = 10

    # Initialize pagination state
    if 'transactions_page' not in st.session_state:
        st.session_state.transactions_page = 0

    # Get total count and calculate pages
    total_transactions = admin_db_manager.get_credit_transactions_count()
    total_pages = max(1, (total_transactions + TRANSACTIONS_PER_PAGE - 1) // TRANSACTIONS_PER_PAGE)

    # Ensure current page is valid
    if st.session_state.transactions_page >= total_pages:
        st.session_state.transactions_page = total_pages - 1
    if st.session_state.transactions_page < 0:
        st.session_state.transactions_page = 0

    current_page = st.session_state.transactions_page
    offset = current_page * TRANSACTIONS_PER_PAGE

    # Get transactions for current page
    transactions = admin_db_manager.get_credit_transactions(limit=TRANSACTIONS_PER_PAGE, offset=offset)

    if transactions:
        df_transactions = pd.DataFrame(transactions)
        df_transactions.columns = ['Usuario', 'Cantidad', 'Tipo', 'Descripción', 'Admin', 'Fecha y Hora']
        st.dataframe(df_transactions, use_container_width=True, hide_index=True)

        # Pagination controls
        col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])

        with col1:
            if st.button("⏮️ Primera", disabled=(current_page == 0), key="trans_first"):
                st.session_state.transactions_page = 0
                st.rerun()

        with col2:
            if st.button("◀️ Anterior", disabled=(current_page == 0), key="trans_prev"):
                st.session_state.transactions_page -= 1
                st.rerun()

        with col3:
            st.markdown(f"<div style='text-align: center; padding: 8px;'>Página **{current_page + 1}** de **{total_pages}** ({total_transactions} transacciones)</div>", unsafe_allow_html=True)

        with col4:
            if st.button("Siguiente ▶️", disabled=(current_page >= total_pages - 1), key="trans_next"):
                st.session_state.transactions_page += 1
                st.rerun()

        with col5:
            if st.button("Última ⏭️", disabled=(current_page >= total_pages - 1), key="trans_last"):
                st.session_state.transactions_page = total_pages - 1
                st.rerun()
    else:
        st.info("No hay transacciones de créditos")


def show_config_tab():
    """Mostrar pestaña de configuración del sistema"""
    st.subheader("⚙️ Configuración del Sistema")

    # Header estilizado
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border: 2px solid #dee2e6;
        border-radius: 15px;
        padding: 20px;
        margin: 20px 0;
        text-align: center;
    ">
        <h3 style="margin: 0; color: #495057;">🔐 Gestión de Contraseña del Candado</h3>
        <p style="margin: 10px 0 0 0; color: #6c757d;">Esta contraseña se enviará en los emails de confirmación de reserva</p>
    </div>
    """, unsafe_allow_html=True)

    # Layout principal
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        # MOVER LA OBTENCIÓN FUERA DEL FORMULARIO
        current_lock_code = admin_db_manager.get_current_lock_code()

        # Card para mostrar contraseña actual - FUERA del formulario
        if current_lock_code:
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
                border: 2px solid #28a745;
                border-radius: 12px;
                padding: 20px;
                margin: 20px 0;
                text-align: center;
                box-shadow: 0 4px 8px rgba(40, 167, 69, 0.2);
            ">
                <h4 style="margin: 0; color: #155724;">
                    <i class="fas fa-lock"></i> Contraseña Actual
                </h4>
                <div style="
                    font-size: 2.5rem;
                    font-weight: bold;
                    color: #155724;
                    margin: 15px 0;
                    font-family: 'Courier New', monospace;
                    background: white;
                    border-radius: 8px;
                    padding: 15px;
                    box-shadow: inset 0 2px 4px rgba(0,0,0,0.1);
                ">
                    {current_lock_code}
                </div>
                <small style="color: #155724; opacity: 0.8;">
                    Esta contraseña se incluye en los emails de confirmación
                </small>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="
                background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
                border: 2px solid #dc3545;
                border-radius: 12px;
                padding: 20px;
                margin: 20px 0;
                text-align: center;
                box-shadow: 0 4px 8px rgba(220, 53, 69, 0.2);
            ">
                <h4 style="margin: 0; color: #721c24;">
                    <i class="fas fa-exclamation-triangle"></i> Sin Contraseña
                </h4>
                <p style="margin: 10px 0 0 0; color: #721c24;">
                    No hay contraseña configurada para el candado
                </p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        # Formulario SOLO para actualizar - SIN mostrar contraseña actual
        with st.form("advanced_lock_code_form", clear_on_submit=True):  # clear_on_submit=True
            st.markdown("**Actualizar contraseña del candado:**")

            # Input con estilo mejorado
            new_lock_code = st.text_input(
                "Nueva contraseña del candado",
                placeholder="Ingresa 4 dígitos (ej: 1234)",
                max_chars=4,
                help="La contraseña debe ser exactamente 4 dígitos numéricos",
                label_visibility="collapsed"
            )

            # Validación en tiempo real
            if new_lock_code:
                if len(new_lock_code) == 4 and new_lock_code.isdigit():
                    st.success("✅ Formato válido")
                else:
                    if len(new_lock_code) < 4:
                        st.warning(f"⚠️ Faltan {4 - len(new_lock_code)} dígito(s)")
                    elif len(new_lock_code) > 4:
                        st.error("❌ Máximo 4 dígitos")
                    elif not new_lock_code.isdigit():
                        st.error("❌ Solo se permiten números")

            st.markdown("<br>", unsafe_allow_html=True)

            # Botón de actualización estilizado
            col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
            with col_btn2:
                submit_button = st.form_submit_button(
                    "🔄 Actualizar Contraseña",
                    type="primary",
                    use_container_width=True
                )

            if submit_button:
                if not new_lock_code:
                    st.error("❌ Por favor ingresa una contraseña")
                elif len(new_lock_code) != 4:
                    st.error("❌ La contraseña debe tener exactamente 4 dígitos")
                elif not new_lock_code.isdigit():
                    st.error("❌ La contraseña solo puede contener números")
                else:
                    # Intentar actualizar
                    admin_user = st.session_state.get('admin_user', {})

                    with st.spinner("🔄 Actualizando contraseña..."):
                        success = admin_db_manager.update_lock_code(
                            new_lock_code,
                            admin_user.get('username', 'admin')
                        )

                    if success:
                        st.success("✅ Contraseña actualizada exitosamente")
                        st.balloons()

                        # Forzar actualización completa
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error("❌ Error al actualizar la contraseña. Intenta de nuevo.")

        # Información adicional
        with st.expander("ℹ️ Información sobre la contraseña del candado", expanded=False):
            st.markdown("""
            **¿Para qué sirve esta contraseña?**
            - Se incluye en todos los emails de confirmación de reserva
            - Los usuarios la necesitan para abrir el candado de la cancha
            - Es importante mantenerla actualizada y comunicarla cuando sea necesario

            **Recomendaciones:**
            - Usa 4 dígitos fáciles de recordar pero no obvios
            - Cambia la contraseña periódicamente por seguridad
            - Evita secuencias simples como 1234 o 0000

            **Historial de cambios:**
            - Los cambios quedan registrados con fecha y administrador
            - Puedes ver el historial en la base de datos si es necesario
            """)

    st.markdown("---")

    # Código de Acceso para Primer Login
    st.markdown("""
        <div style="
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border: 2px solid #dee2e6;
            border-radius: 15px;
            padding: 20px;
            margin: 20px 0;
            text-align: center;
        ">
            <h3 style="margin: 0; color: #495057;">🔐 Código de Acceso Primer Login</h3>
            <p style="margin: 10px 0 0 0; color: #6c757d;">Código requerido para usuarios en su primer acceso al sistema</p>
        </div>
        """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        # Mostrar código actual
        current_access_code = admin_db_manager.get_current_access_code()

        if current_access_code:
            st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, #d1ecf1 0%, #bee5eb 100%);
                    border: 2px solid #17a2b8;
                    border-radius: 12px;
                    padding: 20px;
                    margin: 20px 0;
                    text-align: center;
                    box-shadow: 0 4px 8px rgba(23, 162, 184, 0.2);
                ">
                    <h4 style="margin: 0; color: #0c5460;">
                        <i class="fas fa-key"></i> Código de Acceso Actual
                    </h4>
                    <div style="
                        font-size: 2.5rem;
                        font-weight: bold;
                        color: #0c5460;
                        margin: 15px 0;
                        font-family: 'Courier New', monospace;
                        background: white;
                        border-radius: 8px;
                        padding: 15px;
                        box-shadow: inset 0 2px 4px rgba(0,0,0,0.1);
                    ">
                        {current_access_code}
                    </div>
                    <small style="color: #0c5460; opacity: 0.8;">
                        Proporciona este código a nuevos usuarios para su primer acceso
                    </small>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
                <div style="
                    background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
                    border: 2px solid #dc3545;
                    border-radius: 12px;
                    padding: 20px;
                    margin: 20px 0;
                    text-align: center;
                ">
                    <h4 style="margin: 0; color: #721c24;">
                        <i class="fas fa-exclamation-triangle"></i> Sin Código de Acceso
                    </h4>
                    <p style="margin: 10px 0 0 0; color: #721c24;">
                        No hay código de acceso configurado
                    </p>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("---")

        # Formulario para actualizar código
        with st.form("access_code_form", clear_on_submit=True):
            st.markdown("**Actualizar código de acceso:**")

            new_access_code = st.text_input(
                "Nuevo código de acceso",
                placeholder="Ingresa el código de acceso (ej: ABC123XYZ)",
                max_chars=20,
                help="El código puede tener hasta 20 caracteres (letras y números)",
                label_visibility="collapsed"
            )

            # Validación en tiempo real
            if new_access_code:
                if len(new_access_code) >= 4:
                    st.success(f"✅ Formato válido ({len(new_access_code)} caracteres)")
                else:
                    st.warning(f"⚠️ Mínimo 4 caracteres (tienes {len(new_access_code)})")

            st.markdown("<br>", unsafe_allow_html=True)

            col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
            with col_btn2:
                submit_button = st.form_submit_button(
                    "🔄 Actualizar Código",
                    type="primary",
                    use_container_width=True
                )

            if submit_button:
                if not new_access_code:
                    st.error("❌ Por favor ingresa un código")
                elif len(new_access_code) < 4:
                    st.error("❌ El código debe tener al menos 4 caracteres")
                elif len(new_access_code) > 20:
                    st.error("❌ El código no puede exceder 20 caracteres")
                else:
                    admin_user = st.session_state.get('admin_user', {})

                    with st.spinner("🔄 Actualizando código..."):
                        success = admin_db_manager.update_access_code(
                            new_access_code.upper(),
                            admin_user.get('username', 'admin')
                        )

                    if success:
                        st.success("✅ Código de acceso actualizado exitosamente")
                        st.balloons()
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error("❌ Error al actualizar el código. Intenta de nuevo.")

        # Información adicional
        with st.expander("ℹ️ Información sobre el código de acceso", expanded=False):
            st.markdown("""
                **¿Para qué sirve este código?**
                - Se requiere únicamente en el primer login de cada usuario
                - Después del primer acceso exitoso, ya no se pedirá más
                - Ayuda a controlar el acceso inicial al sistema

                **Recomendaciones:**
                - Usa 6 caracteres fáciles de comunicar
                - Combina letras y números para mayor seguridad
                - Cambia el código periódicamente
                - Comunica el código de manera segura a nuevos usuarios

                **Proceso:**
                1. Nuevo usuario se registra normalmente
                2. En su primer login, se le pide este código
                3. Una vez ingresado correctamente, nunca más se le pedirá
                """)

    st.markdown("---")

    # ========================================
    # ESCUELA DE TENIS
    # ========================================
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
        border: 2px solid #28a745;
        border-radius: 15px;
        padding: 20px;
        margin: 20px 0;
        text-align: center;
    ">
        <h3 style="margin: 0; color: #155724;">🎾 Escuela de Tenis</h3>
        <p style="margin: 10px 0 0 0; color: #155724;">Bloquear Sábados y Domingos 8:00 AM - 12:00 PM</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        is_enabled = admin_db_manager.get_tennis_school_enabled()

        st.markdown(f"""
        <div style="
            text-align: center;
            padding: 15px;
            background: {'#d4edda' if is_enabled else '#f8d7da'};
            border-radius: 10px;
            margin: 15px 0;
        ">
            <p style="margin: 0; font-size: 1.3em; font-weight: bold; color: {'#155724' if is_enabled else '#721c24'};">
                {'✅ ACTIVA' if is_enabled else '❌ INACTIVA'}
            </p>
        </div>
        """, unsafe_allow_html=True)

        if is_enabled:
            if st.button("🔴 Desactivar", key="tennis_school_disable", type="secondary", use_container_width=True):
                admin_username = st.session_state.admin_user.get('username', 'admin')
                success, message = admin_db_manager.set_tennis_school_enabled(False, admin_username)
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
        else:
            if st.button("✅ Activar", key="tennis_school_enable", type="primary", use_container_width=True):
                admin_username = st.session_state.admin_user.get('username', 'admin')
                success, message = admin_db_manager.set_tennis_school_enabled(True, admin_username)
                if success:
                    st.success(message)
                    st.balloons()
                    st.rerun()
                else:
                    st.error(message)

        with st.expander("ℹ️ ¿Qué hace esto?", expanded=False):
            st.markdown("""
            **Cuando está activa:**
            - Todos los sábados y domingos de 8:00 AM a 12:00 PM quedan bloqueados
            - Los usuarios no pueden hacer reservas en estos horarios
            - Los horarios aparecen marcados como "Escuela de Tenis"

            **Cuando está inactiva:**
            - Los sábados y domingos están disponibles para reservas normales
            """)

    st.markdown("---")

    # Gestión de Usuarios del comité
    st.markdown("""
        <div style="
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border: 2px solid #dee2e6;
            border-radius: 15px;
            padding: 20px;
            margin: 20px 0;
            text-align: center;
        ">
            <h3 style="margin: 0; color: #495057;">⭐ Gestión de usuarios que pertenecen al comité</h3>
            <p style="margin: 10px 0 0 0; color: #6c757d;">Los usuarios del comité pueden reservar de 7:55 AM a 8:00 PM</p>
        </div>
        """, unsafe_allow_html=True)

    # Mostrar usuarios VIP actuales
    vip_users = admin_db_manager.get_vip_users()

    if vip_users:
        st.subheader("🏛️ Usuarios que pertenecen al comité")
        for user in vip_users:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"📧 {user['email']}")
            with col2:
                if st.button("❌ Remover", key=f"remove_vip_{user['id']}"):
                    if admin_db_manager.remove_vip_user(user['email']):
                        st.success(f"Usuario removido del Comité: {user['email']}")
                        st.rerun()
                    else:
                        st.error("Error removiendo usuario del comité")

    # Formulario para agregar nuevo usuario al comité
    with st.form("add_vip_user_form", clear_on_submit=True):
        st.markdown("**Agregar nuevo usuario al comité:**")
        new_vip_email = st.text_input(
            "Email del usuario",
            placeholder="usuario@ejemplo.com",
            help="El usuario debe estar registrado en el sistema"
        )

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.form_submit_button("⭐ Agregar al comité", type="primary", use_container_width=True):
                if new_vip_email:
                    admin_user = st.session_state.get('admin_user', {})
                    if admin_db_manager.add_vip_user(new_vip_email, admin_user.get('username', 'admin')):
                        st.success(f"✅ Usuario agregado al comité: {new_vip_email}")
                        st.rerun()
                    else:
                        st.error("❌ Error agregando usuario (puede que ya sea parte del comité o no exista)")
                else:
                    st.error("Por favor ingresa un email válido")


def show_maintenance_tab():
    """Mostrar pestaña de gestión de mantenimiento"""
    st.subheader("🔧 Gestión de Mantenimiento de Cancha")

    # ========================================
    # CHECK FOR SUCCESS MESSAGE FIRST
    # ========================================
    if 'maintenance_success' in st.session_state:
        success_info = st.session_state.maintenance_success

        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
            border: 3px solid #28a745;
            border-radius: 20px;
            padding: 40px;
            margin: 50px auto;
            max-width: 800px;
            text-align: center;
            box-shadow: 0 8px 16px rgba(40, 167, 69, 0.2);
        ">
            <h2 style="margin: 0; color: #155724; font-size: 2.5em;">✅ Mantenimiento Programado Exitosamente</h2>
            <p style="margin: 20px 0; color: #155724; font-size: 1.3em;">{success_info['message']}</p>
            <div style="
                background: rgba(255, 255, 255, 0.8);
                border-radius: 12px;
                padding: 20px;
                margin: 30px auto;
                max-width: 500px;
            ">
                <p style="margin: 8px 0; color: #155724; font-size: 1.1em;"><strong>📅 Fecha:</strong> {success_info['date']}</p>
                <p style="margin: 8px 0; color: #155724; font-size: 1.1em;"><strong>⏰ Horario:</strong> {success_info['start_hour']:02d}:00 - {success_info['end_hour']:02d}:00</p>
                <p style="margin: 8px 0; color: #155724; font-size: 1.1em;"><strong>📝 Motivo:</strong> {success_info['reason']}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("➕ Programar Otro Mantenimiento", type="primary", use_container_width=True, key="program_another"):
                del st.session_state.maintenance_success
                st.rerun()

        return  # Don't show the form after success

    # ========================================
    # MAINTENANCE SECTION
    # ========================================
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border: 2px solid #dee2e6;
        border-radius: 15px;
        padding: 20px;
        margin: 20px 0;
        text-align: center;
    ">
        <h3 style="margin: 0; color: #495057;">🔧 Programar Mantenimiento</h3>
        <p style="margin: 10px 0 0 0; color: #6c757d;">Bloquea horarios cuando la cancha no esté disponible</p>
    </div>
    """, unsafe_allow_html=True)

    # Formulario para agregar mantenimiento
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        with st.form("add_maintenance_form", clear_on_submit=True):
            st.markdown("**Programar nuevo mantenimiento:**")

            # Selector de fecha
            maintenance_date = st.date_input(
                "Fecha de mantenimiento",
                min_value=get_colombia_today(),
                help="Selecciona la fecha para el mantenimiento"
            )

            # Opción de día completo
            is_whole_day = st.checkbox(
                "🔧 Mantenimiento de día completo (6:00 - 22:00)",
                help="Bloquea todas las horas del día (6:00 AM a 10:00 PM)"
            )

            # Selectores de rango de horas (solo si no es día completo)
            if not is_whole_day:
                col_start, col_end = st.columns(2)

                with col_start:
                    start_hour = st.selectbox(
                        "Hora de inicio",
                        options=list(range(6, 22)),
                        format_func=lambda x: f"{x:02d}:00",
                        help="Hora de inicio del mantenimiento"
                    )

                with col_end:
                    end_hour = st.selectbox(
                        "Hora de fin",
                        options=list(range(7, 23)),
                        index=min(15-7, len(list(range(7, 23)))-1),  # Default a las 3 PM
                        format_func=lambda x: f"{x:02d}:00",
                        help="Hora de fin del mantenimiento (no incluida)"
                    )
            else:
                start_hour = 6
                end_hour = 22

            # Motivo
            maintenance_reason = st.text_area(
                "Motivo del mantenimiento",
                placeholder="Ej: Limpieza profunda, reparación de superficie, pintura, etc.",
                max_chars=200
            )

            # Botón de submit
            col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
            with col_btn2:
                submit_button = st.form_submit_button(
                    "🔧 Programar Mantenimiento",
                    type="primary",
                    use_container_width=True
                )

            if submit_button:
                # Validar horas
                if not is_whole_day and start_hour >= end_hour:
                    st.error("❌ La hora de inicio debe ser menor que la hora de fin")
                else:
                    admin_user = st.session_state.get('admin_user', {})

                    success, message = admin_db_manager.add_maintenance_slot(
                        maintenance_date.strftime('%Y-%m-%d'),
                        start_hour,
                        end_hour,
                        maintenance_reason.strip() if maintenance_reason else "Mantenimiento programado",
                        admin_user.get('username', 'admin'),
                        is_whole_day
                    )

                    if success:
                        # Store success info in session state
                        st.session_state.maintenance_success = {
                            'message': message,
                            'date': maintenance_date.strftime('%Y-%m-%d'),
                            'start_hour': start_hour,
                            'end_hour': end_hour,
                            'reason': maintenance_reason.strip() if maintenance_reason else "Mantenimiento programado"
                        }
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")

    st.markdown("---")

    # Mostrar mantenimientos programados
    st.subheader("📋 Mantenimientos Programados")

    # Controles
    col1, col2 = st.columns([2, 1])

    with col1:
        days_range = st.selectbox(
            "Mostrar mantenimientos de:",
            options=[7, 15, 30, 60, 90],
            index=1,
            format_func=lambda x: f"Próximos {x} días"
        )

    with col2:
        if st.button("🔄 Actualizar", key="refresh_maintenance"):
            st.cache_data.clear()
            st.success("✅ Actualizado")

    # Obtener mantenimientos
    from datetime import timedelta
    start_date = get_colombia_today().strftime('%Y-%m-%d')
    end_date = (get_colombia_today() + timedelta(days=days_range)).strftime('%Y-%m-%d')

    blocked_slots = admin_db_manager.get_blocked_slots(start_date, end_date)

    if blocked_slots:
        st.info(f"📊 Total de mantenimientos programados: {len(blocked_slots)}")

        # Mostrar cada mantenimiento
        for slot in blocked_slots:
            # Formatear fecha
            from timezone_utils import format_date_display
            date_display = format_date_display(slot['date'])

            # Determinar el tipo de mantenimiento y formato de hora
            maintenance_type = slot.get('maintenance_type', 'single_hour')
            start_hour = slot.get('start_hour', slot.get('hour', 6))
            end_hour = slot.get('end_hour', slot.get('hour', 6) + 1)

            if maintenance_type == 'whole_day':
                hour_display = "🌅 DÍA COMPLETO (6:00 - 22:00)"
                type_badge = "🔧 Día Completo"
            elif maintenance_type == 'time_range':
                hour_display = f"⏰ {start_hour:02d}:00 - {end_hour:02d}:00"
                hours_count = slot.get('hour_count', end_hour - start_hour)
                type_badge = f"⏱️ Rango ({hours_count}h)"
            else:
                hour_display = f"{start_hour:02d}:00 - {end_hour:02d}:00"
                type_badge = "🕐 Individual"

            with st.expander(f"🔧 {date_display} • {hour_display}", expanded=False):
                col1, col2 = st.columns([3, 1])

                with col1:
                    st.markdown(f"""
                    **📅 Fecha:** {date_display}
                    **🕐 Horario:** {hour_display}
                    **🏷️ Tipo:** {type_badge}
                    **📝 Motivo:** {slot.get('reason', 'No especificado')}
                    **👤 Programado por:** {slot.get('created_by', 'N/A')}
                    **📆 Creado:** {slot.get('created_at', 'N/A')}
                    """)

                    # Mostrar detalles de horas individuales bloqueadas si es rango
                    if maintenance_type in ['time_range', 'whole_day']:
                        hours_list = slot.get('hours_list', [])
                        if hours_list:
                            st.caption(f"🔒 Horas bloqueadas: {', '.join([f'{h:02d}:00' for h in sorted(hours_list)])}")

                with col2:
                    # Botón para eliminar
                    delete_key = f"delete_maintenance_{slot['date']}_{start_hour}_{end_hour}"
                    if st.button("🗑️ Eliminar", key=delete_key):
                        # Si es un rango, eliminar todos los slots del rango
                        if maintenance_type in ['time_range', 'whole_day']:
                            success, message = admin_db_manager.remove_maintenance_range(
                                slot['date'], start_hour, end_hour
                            )
                            if success:
                                st.success(f"✅ {message}")
                                import time
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error(f"❌ {message}")
                        else:
                            # Eliminar slot individual
                            if admin_db_manager.remove_maintenance_slot(slot['id']):
                                st.success("✅ Mantenimiento eliminado")
                                import time
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("❌ Error al eliminar")
    else:
        st.info("📅 No hay mantenimientos programados en este período")

def main():
    """Función principal de la aplicación de administración"""
    setup_admin_page_config()
    apply_admin_styles()

    # Validate admin security configuration first
    if not admin_auth_manager.validate_admin_config():
        st.error("🚨 Admin security configuration failed")
        st.stop()

    # Ensure admin user exists with secure credentials
    if not admin_auth_manager.ensure_admin_user_exists():
        st.error("🚨 Failed to initialize admin user")
        st.stop()

    # Verificar autenticación
    if not require_admin_auth():
        show_admin_login()
    else:
        show_admin_dashboard()


if __name__ == "__main__":
    main()