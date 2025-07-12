"""
Admin Tab for Tennis Court Reservation System
Handles the administration interface
"""

import streamlit as st
import datetime
from datetime import timedelta
import pandas as pd
from database_manager import db_manager

# Configuración de administración
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "tennis123"

def format_hour(hour: int) -> str:
    """Formatear hora para mostrar"""
    return f"{hour:02d}:00"

def format_date(date_str: str) -> str:
    """Formatear fecha en español"""
    try:
        date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
        days = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        months = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                  'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
        
        day_name = days[date_obj.weekday()]
        month_name = months[date_obj.month - 1]
        
        return f"{day_name}, {date_obj.day} de {month_name} de {date_obj.year}"
    except:
        return date_str

def show_admin_tab():
    """Mostrar la pestaña de administración"""
    if not st.session_state.get('admin_logged_in', False):
        show_admin_login()
    else:
        show_admin_dashboard()

def show_admin_login():
    """Mostrar interfaz de login de administrador"""
    st.header("🔐 Acceso de Administrador")
    
    # Centrar el formulario
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.container():
            st.markdown("### 👤 Iniciar Sesión")
            
            with st.form("admin_login", clear_on_submit=False):
                username = st.text_input(
                    "👤 Usuario", 
                    placeholder="Ingresa tu usuario",
                    help="Usuario administrador del sistema"
                )
                
                password = st.text_input(
                    "🔑 Contraseña", 
                    type="password", 
                    placeholder="Ingresa tu contraseña",
                    help="Contraseña del administrador"
                )
                
                # Botón de login
                login_button = st.form_submit_button(
                    "🚪 Iniciar Sesión", 
                    use_container_width=True,
                    type="primary"
                )
                
                if login_button:
                    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
                        st.session_state.admin_logged_in = True
                        st.success("✅ Acceso concedido")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error("❌ Credenciales incorrectas")
                        if username and password:  # Solo mostrar si se ingresaron datos
                            st.warning("⚠️ Verifica tu usuario y contraseña")
            
            # Mostrar credenciales para demo (remover en producción)
            with st.expander("💡 Credenciales de prueba", expanded=False):
                st.info(f"""
                **Para fines de demostración:**
                
                👤 **Usuario:** `{ADMIN_USERNAME}`
                
                🔑 **Contraseña:** `{ADMIN_PASSWORD}`
                """)
                st.caption("⚠️ En producción, estas credenciales no se mostrarían.")

def show_admin_dashboard():
    """Mostrar el panel de administración"""
    st.header("⚙️ Panel de Administración")
    
    # Barra superior con información del admin y logout
    col1, col2, col3 = st.columns([3, 2, 1])
    
    with col1:
        st.markdown(f"👋 **Bienvenido, {ADMIN_USERNAME}**")
    
    with col2:
        current_time = datetime.datetime.now()
        st.caption(f"🕐 {current_time.strftime('%d/%m/%Y %H:%M:%S')}")
    
    with col3:
        if st.button("🚪 Cerrar Sesión", type="secondary"):
            st.session_state.admin_logged_in = False
            # Limpiar otros estados de admin si existen
            for key in list(st.session_state.keys()):
                if key.startswith('admin_'):
                    del st.session_state[key]
            st.rerun()
    
    st.divider()
    
    # Pestañas del panel de administración
    admin_tabs = st.tabs([
        "📋 Gestión de Reservas", 
        "📊 Dashboard & Estadísticas", 
        "⚙️ Configuración del Sistema",
        "🔧 Mantenimiento"
    ])
    
    with admin_tabs[0]:
        show_reservations_management()
    
    with admin_tabs[1]:
        show_statistics_dashboard()
    
    with admin_tabs[2]:
        show_configuration_panel()
    
    with admin_tabs[3]:
        show_maintenance_panel()

def show_reservations_management():
    """Mostrar gestión completa de reservas"""
    st.subheader("📋 Gestión de Reservas")
    
    # Obtener todas las reservas
    reservations = db_manager.get_all_reservations()
    
    if not reservations:
        st.info("📭 No hay reservas registradas en el sistema")
        return
    
    # Métricas rápidas
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📝 Total Reservas", len(reservations))
    
    with col2:
        unique_users = len(set([r[3] for r in reservations]))  # r[3] es email
        st.metric("👥 Usuarios Únicos", unique_users)
    
    with col3:
        today = datetime.date.today()
        tomorrow = today + timedelta(days=1)
        tomorrow_count = len([r for r in reservations if r[0] == tomorrow.strftime('%Y-%m-%d')])
        st.metric("📅 Reservas Mañana", tomorrow_count)
    
    with col4:
        # Reservas de esta semana
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        week_count = len([
            r for r in reservations 
            if week_start.strftime('%Y-%m-%d') <= r[0] <= week_end.strftime('%Y-%m-%d')
        ])
        st.metric("📊 Esta Semana", week_count)
    
    st.divider()
    
    # Filtros avanzados
    with st.expander("🔍 Filtros Avanzados", expanded=True):
        filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)
        
        with filter_col1:
            # Filtro por fecha
            dates = sorted(list(set([r[0] for r in reservations])), reverse=True)
            selected_date = st.selectbox(
                "📅 Filtrar por fecha",
                ["Todas las fechas"] + dates,
                help="Selecciona una fecha específica"
            )
        
        with filter_col2:
            # Filtro por usuario (nombre)
            users = sorted(list(set([r[2] for r in reservations])))
            selected_user = st.selectbox(
                "👤 Filtrar por usuario",
                ["Todos los usuarios"] + users,
                help="Selecciona un usuario específico"
            )
        
        with filter_col3:
            # Filtro por hora
            hours = sorted(list(set([r[1] for r in reservations])))
            selected_hour = st.selectbox(
                "⏰ Filtrar por hora",
                ["Todas las horas"] + [format_hour(h) for h in hours],
                help="Selecciona una hora específica"
            )
        
        with filter_col4:
            # Filtro por período
            period_filter = st.selectbox(
                "📊 Período",
                ["Todos", "Hoy", "Mañana", "Esta semana", "Este mes"],
                help="Filtrar por período de tiempo"
            )
    
    # Aplicar filtros
    filtered_reservations = reservations.copy()
    
    # Filtro por fecha
    if selected_date != "Todas las fechas":
        filtered_reservations = [r for r in filtered_reservations if r[0] == selected_date]
    
    # Filtro por usuario
    if selected_user != "Todos los usuarios":
        filtered_reservations = [r for r in filtered_reservations if r[2] == selected_user]
    
    # Filtro por hora
    if selected_hour != "Todas las horas":
        hour_value = int(selected_hour.split(':')[0])
        filtered_reservations = [r for r in filtered_reservations if r[1] == hour_value]
    
    # Filtro por período
    if period_filter != "Todos":
        today = datetime.date.today()
        tomorrow = today + timedelta(days=1)
        
        if period_filter == "Hoy":
            filtered_reservations = [r for r in filtered_reservations if r[0] == today.strftime('%Y-%m-%d')]
        elif period_filter == "Mañana":
            filtered_reservations = [r for r in filtered_reservations if r[0] == tomorrow.strftime('%Y-%m-%d')]
        elif period_filter == "Esta semana":
            week_start = today - timedelta(days=today.weekday())
            week_end = week_start + timedelta(days=6)
            filtered_reservations = [
                r for r in filtered_reservations 
                if week_start.strftime('%Y-%m-%d') <= r[0] <= week_end.strftime('%Y-%m-%d')
            ]
        elif period_filter == "Este mes":
            month_start = today.replace(day=1)
            next_month = month_start.replace(month=month_start.month % 12 + 1)
            month_end = next_month - timedelta(days=1)
            filtered_reservations = [
                r for r in filtered_reservations 
                if month_start.strftime('%Y-%m-%d') <= r[0] <= month_end.strftime('%Y-%m-%d')
            ]
    
    # Mostrar resultados filtrados
    st.write(f"**Mostrando:** {len(filtered_reservations)} reserva(s) de {len(reservations)} total")
    
    if filtered_reservations:
        # Botones de acción masiva
        action_col1, action_col2, action_col3 = st.columns([1, 1, 2])
        
        with action_col1:
            if st.button("🔄 Actualizar", use_container_width=True):
                st.rerun()
        
        with action_col2:
            if st.button("📥 Exportar Filtro", use_container_width=True):
                # Crear CSV con datos filtrados
                csv_data = "Fecha,Hora,Nombre,Email,Creado\n"
                for r in filtered_reservations:
                    date_str, hour, name, email, created_at, res_id = r
                    csv_data += f'"{date_str}","{format_hour(hour)}","{name}","{email}","{created_at}"\n'
                
                st.download_button(
                    label="💾 Descargar CSV",
                    data=csv_data,
                    file_name=f"reservas_filtradas_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
        
        st.divider()
        
        # Tabla de reservas con paginación
        items_per_page = 10
        total_pages = (len(filtered_reservations) + items_per_page - 1) // items_per_page
        
        if total_pages > 1:
            page = st.selectbox(
                f"📄 Página (Total: {total_pages})",
                range(1, total_pages + 1),
                key="reservations_page"
            )
            start_idx = (page - 1) * items_per_page
            end_idx = min(start_idx + items_per_page, len(filtered_reservations))
            page_reservations = filtered_reservations[start_idx:end_idx]
        else:
            page_reservations = filtered_reservations
        
        # Encabezados de tabla
        header_col1, header_col2, header_col3, header_col4, header_col5, header_col6 = st.columns([2, 1.5, 2, 2.5, 2, 1])
        
        with header_col1:
            st.markdown("**📅 Fecha**")
        with header_col2:
            st.markdown("**⏰ Hora**")
        with header_col3:
            st.markdown("**👤 Nombre**")
        with header_col4:
            st.markdown("**📧 Email**")
        with header_col5:
            st.markdown("**🕐 Creado**")
        with header_col6:
            st.markdown("**🗑️ Acción**")
        
        st.divider()
        
        # Mostrar cada reserva
        for reservation in page_reservations:
            date_str, hour, name, email, created_at, res_id = reservation
            
            col1, col2, col3, col4, col5, col6 = st.columns([2, 1.5, 2, 2.5, 2, 1])
            
            with col1:
                st.write(f"📅 {format_date(date_str)}")
            
            with col2:
                st.write(f"⏰ {format_hour(hour)}")
            
            with col3:
                # Truncar nombre si es muy largo
                display_name = name[:20] + "..." if len(name) > 20 else name
                st.write(f"👤 {display_name}")
            
            with col4:
                # Truncar email si es muy largo
                display_email = email[:25] + "..." if len(email) > 25 else email
                st.write(f"📧 {display_email}")
            
            with col5:
                created_date = created_at[:16] if created_at else "N/A"
                st.write(f"🕐 {created_date}")
            
            with col6:
                if st.button(
                    "🗑️", 
                    key=f"delete_{res_id}", 
                    help=f"Eliminar reserva de {name}",
                    use_container_width=True
                ):
                    if db_manager.delete_reservation_by_id(res_id):
                        st.success(f"✅ Reserva de {name} eliminada")
                        st.rerun()
                    else:
                        st.error("❌ Error al eliminar la reserva")
            
            st.divider()
    else:
        st.info("🔍 No se encontraron reservas con los filtros aplicados")

def show_statistics_dashboard():
    """Mostrar dashboard completo de estadísticas"""
    st.subheader("📊 Dashboard & Estadísticas")
    
    # Obtener estadísticas
    stats = db_manager.get_reservation_statistics()
    
    if stats['total_reservations'] == 0:
        st.info("📭 No hay datos suficientes para mostrar estadísticas")
        return
    
    # Métricas principales
    st.markdown("### 📈 Métricas Principales")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "📝 Total Reservas", 
            stats['total_reservations'],
            help="Número total de reservas registradas"
        )
    
    with col2:
        st.metric(
            "👥 Usuarios Únicos", 
            stats['unique_users'],
            help="Número de usuarios diferentes"
        )
    
    with col3:
        if stats['unique_users'] > 0:
            avg_per_user = stats['total_reservations'] / stats['unique_users']
            st.metric(
                "📈 Promedio/Usuario", 
                f"{avg_per_user:.1f}",
                help="Promedio de reservas por usuario"
            )
        else:
            st.metric("📈 Promedio/Usuario", "0")
    
    with col4:
        # Calcular tasa de ocupación de mañana
        tomorrow = datetime.date.today() + timedelta(days=1)
        tomorrow_reservations = db_manager.get_reservations(tomorrow)
        occupancy_rate = (len(tomorrow_reservations) / 16) * 100  # 16 horarios totales
        st.metric(
            "📊 Ocupación Mañana", 
            f"{occupancy_rate:.1f}%",
            help="Porcentaje de ocupación para mañana"
        )
    
    st.divider()
    
    # Gráficos y análisis
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        st.markdown("### 📅 Reservas por Fecha")
        
        if stats['reservations_by_date']:
            # Preparar datos para el gráfico
            dates = []
            counts = []
            
            for date_str, count in stats['reservations_by_date']:
                try:
                    date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d')
                    dates.append(date_obj.strftime('%d/%m'))
                    counts.append(count)
                except:
                    dates.append(date_str)
                    counts.append(count)
            
            # Crear DataFrame para el gráfico
            chart_data = pd.DataFrame({
                'Fecha': dates,
                'Reservas': counts
            })
            
            st.bar_chart(chart_data.set_index('Fecha'))
        else:
            st.info("No hay datos suficientes para el gráfico")
    
    with chart_col2:
        st.markdown("### ⏰ Horarios Más Populares")
        
        if stats['popular_hours']:
            hours_data = []
            counts_data = []
            
            for hour, count in stats['popular_hours'][:8]:  # Top 8
                hours_data.append(format_hour(hour))
                counts_data.append(count)
            
            hours_chart_data = pd.DataFrame({
                'Hora': hours_data,
                'Reservas': counts_data
            })
            
            st.bar_chart(hours_chart_data.set_index('Hora'))
        else:
            st.info("No hay datos de horarios disponibles")
    
    # Análisis adicional
    analysis_col1, analysis_col2 = st.columns(2)
    
    with analysis_col1:
        st.markdown("### 🏆 Usuarios Más Activos")
        
        if stats['top_users']:
            for i, (name, email, count) in enumerate(stats['top_users'][:5], 1):
                with st.container():
                    medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"#{i}"
                    st.write(f"{medal} **{name}**")
                    st.caption(f"📧 {email} • {count} reserva{'s' if count > 1 else ''}")
                    st.divider()
        else:
            st.info("No hay datos de usuarios disponibles")
    
    with analysis_col2:
        st.markdown("### 📊 Reservas por Día de la Semana")
        
        if stats['reservations_by_weekday']:
            weekday_data = []
            weekday_counts = []
            
            for day_name, count in stats['reservations_by_weekday']:
                weekday_data.append(day_name)
                weekday_counts.append(count)
            
            weekday_chart_data = pd.DataFrame({
                'Día': weekday_data,
                'Reservas': weekday_counts
            })
            
            st.bar_chart(weekday_chart_data.set_index('Día'))
        else:
            st.info("No hay datos por día de semana")
    
    # Análisis temporal
    st.divider()
    st.markdown("### 🕐 Análisis Temporal")
    
    temporal_col1, temporal_col2, temporal_col3 = st.columns(3)
    
    with temporal_col1:
        # Reservas de hoy y mañana
        today = datetime.date.today()
        tomorrow = today + timedelta(days=1)
        
        all_reservations = db_manager.get_all_reservations()
        today_count = len([r for r in all_reservations if r[0] == today.strftime('%Y-%m-%d')])
        tomorrow_count = len([r for r in all_reservations if r[0] == tomorrow.strftime('%Y-%m-%d')])
        
        st.metric("📅 Hoy", today_count)
        st.metric("📅 Mañana", tomorrow_count)
    
    with temporal_col2:
        # Reservas de esta semana
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        
        week_reservations = [
            r for r in all_reservations 
            if week_start.strftime('%Y-%m-%d') <= r[0] <= week_end.strftime('%Y-%m-%d')
        ]
        
        st.metric("📊 Esta Semana", len(week_reservations))
        
        # Promedio diario de la semana
        if len(week_reservations) > 0:
            avg_daily = len(week_reservations) / 7
            st.metric("📈 Promedio Diario", f"{avg_daily:.1f}")
    
    with temporal_col3:
        # Reservas de este mes
        month_start = today.replace(day=1)
        try:
            if today.month == 12:
                next_month = month_start.replace(year=today.year + 1, month=1)
            else:
                next_month = month_start.replace(month=today.month + 1)
            month_end = next_month - timedelta(days=1)
        except:
            month_end = today
        
        month_reservations = [
            r for r in all_reservations 
            if month_start.strftime('%Y-%m-%d') <= r[0] <= month_end.strftime('%Y-%m-%d')
        ]
        
        st.metric("📅 Este Mes", len(month_reservations))
        
        # Tasa de crecimiento mensual (si hay datos del mes anterior)
        try:
            prev_month_start = (month_start - timedelta(days=1)).replace(day=1)
            prev_month_end = month_start - timedelta(days=1)
            
            prev_month_reservations = [
                r for r in all_reservations 
                if prev_month_start.strftime('%Y-%m-%d') <= r[0] <= prev_month_end.strftime('%Y-%m-%d')
            ]
            
            if len(prev_month_reservations) > 0:
                growth_rate = ((len(month_reservations) - len(prev_month_reservations)) / len(prev_month_reservations)) * 100
                st.metric("📈 Crecimiento", f"{growth_rate:+.1f}%")
        except:
            pass

def show_configuration_panel():
    """Mostrar panel de configuración del sistema"""
    st.subheader("⚙️ Configuración del Sistema")
    
    # Configuración actual
    with st.expander("📋 Configuración Actual", expanded=True):
        config_col1, config_col2 = st.columns(2)
        
        with config_col1:
            st.markdown("""
            **🎾 Reglas de Reserva:**
            - Solo reservas para el día siguiente
            - Máximo 2 horas por usuario por día
            - No reservas en días consecutivos
            - Horas deben ser consecutivas
            - Horarios: 6:00 AM - 9:00 PM (16 slots)
            """)
        
        with config_col2:
            st.markdown("""
            **🔧 Configuración Técnica:**
            - Base de datos: SQLite
            - Archivo: tennis_reservations.db
            - Framework: Streamlit
            - Autenticación: Usuario/Contraseña
            - Backup: Manual (CSV export)
            """)
    
    # Acciones de administración
    st.divider()
    st.markdown("### 🛠️ Acciones de Administración")
    
    action_col1, action_col2, action_col3 = st.columns(3)
    
    with action_col1:
        st.markdown("**📥 Exportar Datos**")
        
        if st.button("📄 Generar Reporte Completo", use_container_width=True):
            csv_content = db_manager.export_reservations_csv()
            
            if csv_content and len(csv_content.split('\n')) > 2:
                # Agregar información adicional al CSV
                stats = db_manager.get_reservation_statistics()
                timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                enhanced_csv = f"""# Reporte de Reservas - Cancha de Tenis
# Generado: {timestamp}
# Total Reservas: {stats['total_reservations']}
# Usuarios Únicos: {stats['unique_users']}
# 
{csv_content}"""
                
                st.download_button(
                    label="💾 Descargar Reporte CSV",
                    data=enhanced_csv,
                    file_name=f"reporte_completo_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
                st.success("✅ Reporte generado")
            else:
                st.warning("⚠️ No hay datos para exportar")
    
    with action_col2:
        st.markdown("**🗑️ Limpiar Datos**")
        
        if 'confirm_clear' not in st.session_state:
            st.session_state.confirm_clear = False
        
        if not st.session_state.confirm_clear:
            if st.button("🗑️ Limpiar Todas las Reservas", use_container_width=True):
                st.session_state.confirm_clear = True
                st.rerun()
        else:
            st.warning("⚠️ **¿Estás seguro?**")
            st.caption("Esta acción eliminará TODAS las reservas permanentemente")
            
            confirm_col1, confirm_col2 = st.columns(2)
            
            with confirm_col1:
                if st.button("✅ Confirmar", type="primary", use_container_width=True):
                    if db_manager.clear_all_reservations():
                        st.success("✅ Todas las reservas eliminadas")
                        st.session_state.confirm_clear = False
                        st.rerun()
                    else:
                        st.error("❌ Error al eliminar reservas")
            
            with confirm_col2:
                if st.button("❌ Cancelar", use_container_width=True):
                    st.session_state.confirm_clear = False
                    st.rerun()
    
    with action_col3:
        st.markdown("**🔄 Optimización**")
        
        if st.button("🔧 Optimizar Base de Datos", use_container_width=True):
            if db_manager.vacuum_database():
                st.success("✅ Base de datos optimizada")
            else:
                st.error("❌ Error al optimizar")
        
        if st.button("📊 Recalcular Estadísticas", use_container_width=True):
            # Forzar recálculo obteniendo estadísticas nuevamente
            stats = db_manager.get_reservation_statistics()
            st.success(f"✅ Estadísticas recalculadas ({stats['total_reservations']} reservas)")

def show_maintenance_panel():
    """Mostrar panel de mantenimiento y información técnica"""
    st.subheader("🔧 Mantenimiento del Sistema")
    
    # Información de la base de datos
    st.markdown("### 💾 Información de Base de Datos")
    
    try:
        db_info = db_manager.get_database_info()
        
        info_col1, info_col2, info_col3 = st.columns(3)
        
        with info_col1:
            st.metric("📁 Archivo BD", db_info.get('database_file', 'N/A'))
            st.metric("💽 Tamaño", f"{db_info.get('database_size_mb', 0):.2f} MB")
        
        with info_col2:
            st.metric("📊 Tablas", len(db_info.get('tables', [])))
            st.metric("📝 Total Registros", db_info.get('total_records', 0))
        
        with info_col3:
            st.metric("🗄️ Reservas", db_info.get('table_sizes', {}).get('reservations', 0))
            st.metric("👥 Usuarios", db_info.get('table_sizes', {}).get('user_reservations', 0))
        
        # Detalles técnicos
        with st.expander("🔍 Detalles Técnicos", expanded=False):
            st.json(db_info)
    
    except Exception as e:
        st.error(f"Error obteniendo información de BD: {str(e)}")
    
    st.divider()
    
    # Herramientas de mantenimiento
    st.markdown("### 🛠️ Herramientas de Mantenimiento")
    
    maint_col1, maint_col2 = st.columns(2)
    
    with maint_col1:
        st.markdown("**🔄 Sistema**")
        
        if st.button("🔄 Reiniciar Estado de Sesión", use_container_width=True):
            # Limpiar estado de sesión relacionado con admin
            keys_to_clear = [k for k in st.session_state.keys() if k.startswith(('admin_', 'reservation_', 'selected_'))]
            for key in keys_to_clear:
                del st.session_state[key]
            st.success("✅ Estado de sesión reiniciado")
            st.rerun()
        
        if st.button("🧪 Verificar Integridad BD", use_container_width=True):
            try:
                # Verificar integridad básica
                reservations = db_manager.get_all_reservations()
                stats = db_manager.get_reservation_statistics()
                
                # Verificaciones básicas
                issues = []
                
                # Verificar fechas válidas
                for reservation in reservations:
                    try:
                        datetime.datetime.strptime(reservation[0], '%Y-%m-%d')
                    except:
                        issues.append(f"Fecha inválida: {reservation[0]}")
                
                # Verificar horas válidas
                for reservation in reservations:
                    if not (6 <= reservation[1] <= 21):
                        issues.append(f"Hora inválida: {reservation[1]}")
                
                if issues:
                    st.warning(f"⚠️ Se encontraron {len(issues)} problemas:")
                    for issue in issues[:5]:  # Mostrar solo los primeros 5
                        st.write(f"• {issue}")
                else:
                    st.success("✅ Integridad verificada - No se encontraron problemas")
                    
            except Exception as e:
                st.error(f"❌ Error verificando integridad: {str(e)}")
    
    with maint_col2:
        st.markdown("**📊 Logs y Monitoreo**")
        
        if st.button("📋 Mostrar Actividad Reciente", use_container_width=True):
            try:
                # Mostrar las últimas 10 reservas
                reservations = db_manager.get_all_reservations()
                recent_reservations = sorted(reservations, key=lambda x: x[4], reverse=True)[:10]
                
                st.markdown("**🕐 Últimas 10 Reservas:**")
                for i, reservation in enumerate(recent_reservations, 1):
                    date_str, hour, name, email, created_at, res_id = reservation
                    st.write(f"{i}. {name} - {format_date(date_str)} {format_hour(hour)} ({created_at[:16]})")
                    
            except Exception as e:
                st.error(f"Error obteniendo actividad: {str(e)}")
        
        if st.button("🔍 Detectar Duplicados", use_container_width=True):
            try:
                reservations = db_manager.get_all_reservations()
                
                # Detectar posibles duplicados por fecha/hora
                seen = set()
                duplicates = []
                
                for reservation in reservations:
                    key = (reservation[0], reservation[1])  # fecha, hora
                    if key in seen:
                        duplicates.append(key)
                    seen.add(key)
                
                if duplicates:
                    st.warning(f"⚠️ Se detectaron {len(duplicates)} posibles duplicados")
                    for date_str, hour in duplicates[:5]:
                        st.write(f"• {format_date(date_str)} {format_hour(hour)}")
                else:
                    st.success("✅ No se detectaron duplicados")
                    
            except Exception as e:
                st.error(f"Error detectando duplicados: {str(e)}")
    
    # Información del sistema
    st.divider()
    st.markdown("### ℹ️ Información del Sistema")
    
    system_col1, system_col2 = st.columns(2)
    
    with system_col1:
        current_time = datetime.datetime.now()
        st.write(f"**🕐 Hora del sistema:** {current_time.strftime('%d/%m/%Y %H:%M:%S')}")
        
        tomorrow = datetime.date.today() + timedelta(days=1)
        st.write(f"**📅 Próxima fecha reservable:** {format_date(tomorrow.strftime('%Y-%m-%d'))}")
        
        st.write(f"**👤 Usuario administrador:** {ADMIN_USERNAME}")
    
    with system_col2:
        st.write("**🔧 Versión del sistema:** 1.0.0")
        st.write("**📚 Framework:** Streamlit")
        st.write("**💾 Base de datos:** SQLite3")
        
        # Tiempo de sesión del admin
        if 'admin_login_time' not in st.session_state:
            st.session_state.admin_login_time = current_time
        
        session_duration = current_time - st.session_state.admin_login_time
        st.write(f"**⏱️ Tiempo de sesión:** {str(session_duration).split('.')[0]}")

# Inicializar estado de sesión para la pestaña de administración
def init_admin_session_state():
    """Inicializar estado de sesión para la pestaña de administración"""
    if 'admin_logged_in' not in st.session_state:
        st.session_state.admin_logged_in = False
    if 'confirm_clear' not in st.session_state:
        st.session_state.confirm_clear = False
    if 'admin_login_time' not in st.session_state:
        st.session_state.admin_login_time = datetime.datetime.now()