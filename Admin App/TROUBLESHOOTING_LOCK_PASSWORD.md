# 🔍 Troubleshooting - Cambio de Contraseña del Candado

## Estado Actual

Hemos agregado **logging detallado** para diagnosticar el problema con el cambio de contraseña del candado.

## 📋 Pasos para Diagnosticar el Problema

### 1. Reinicia la Admin App

```bash
cd "Tennis-Reservation-App/Admin App"
streamlit run admin_app.py
```

### 2. Intenta Cambiar la Contraseña

1. Ve a la pestaña **"⚙️ Config"**
2. Ingresa un nuevo código de 4 dígitos (ej: `1234`)
3. Haz clic en **"🔄 Actualizar Contraseña"**
4. **IMPORTANTE**: Observa la terminal donde se está ejecutando Streamlit

### 3. Busca estos Mensajes en la Terminal

```
[DEBUG] Starting lock code update...
[DEBUG] New code: 1234
[DEBUG] Admin username: admin
[DEBUG] Attempting database insert...
[DEBUG] Database result: <resultado>
[DEBUG] Result data: <datos>
```

---

## 🚨 Errores Comunes y Soluciones

### Error 1: "Connection Error" o "Network Error"

**Causa:** No hay conexión a Supabase o las credenciales son incorrectas.

**Solución:**
1. Verifica que el archivo de secrets de Streamlit existe
2. Ubicación esperada: `/home/user/Tennis-Reservation-App/Admin App/.streamlit/secrets.toml`
3. Debe contener:
   ```toml
   [supabase]
   url = "TU_SUPABASE_URL"
   key = "TU_SUPABASE_KEY"
   ```

### Error 2: "Failed to insert lock code - no data returned"

**Causa:** El insert se ejecutó pero no retornó datos (puede ser un problema de RLS policies).

**Solución:**
1. Verifica las políticas RLS en Supabase para la tabla `lock_code`
2. Asegúrate de que el **service role key** está siendo usado (no el anon key)
3. En Supabase Dashboard → SQL Editor, ejecuta:
   ```sql
   SELECT * FROM lock_code ORDER BY created_at DESC LIMIT 5;
   ```
   Si ves registros, el insert está funcionando pero hay un problema con la respuesta.

### Error 3: "column 'X' does not exist"

**Causa:** Ya corregimos este error (admin_user), pero podría haber otro similar.

**Solución:**
1. Lee el mensaje de error completo en la terminal
2. Verifica que la tabla `lock_code` tiene la estructura correcta:
   ```sql
   SELECT column_name, data_type
   FROM information_schema.columns
   WHERE table_name = 'lock_code';
   ```

### Error 4: "Permission denied" o "RLS policy violation"

**Causa:** Las políticas de Row Level Security (RLS) están bloqueando el insert.

**Solución:**
1. Verifica que estás usando el **service_role** key en secrets.toml (no anon key)
2. En Supabase, verifica las políticas RLS de `lock_code`:
   ```sql
   SELECT * FROM pg_policies WHERE tablename = 'lock_code';
   ```

---

## 🔧 Verificación de Configuración

### Paso 1: Verifica las Secrets de Streamlit

```bash
cat "Tennis-Reservation-App/Admin App/.streamlit/secrets.toml"
```

**Debe mostrar:**
```toml
[supabase]
url = "https://XXXXXX.supabase.co"
key = "eyXXXXXXXXXXXXXXXXX"  # Debe ser SERVICE_ROLE key (empieza con eyJ...)
```

### Paso 2: Verifica la Conexión a Supabase

En la terminal de Python:
```python
python3
>>> from database_manager import db_manager
>>> db_manager.client.table('lock_code').select('*').limit(1).execute()
```

Si muestra un error, el problema es de conexión/credenciales.

### Paso 3: Verifica la Tabla lock_code

En Supabase Dashboard → SQL Editor:
```sql
-- Ver estructura de la tabla
\d lock_code;

-- Ver registros recientes
SELECT * FROM lock_code ORDER BY created_at DESC LIMIT 5;

-- Intentar insertar manualmente
INSERT INTO lock_code (code) VALUES ('9999');
```

Si el insert manual funciona, el problema está en el código de Python.
Si falla, el problema está en la configuración de Supabase.

---

## 📊 Logs Esperados (Funcionando Correctamente)

Si todo funciona bien, deberías ver:

```
[DEBUG] Starting lock code update...
[DEBUG] New code: 1234
[DEBUG] Admin username: admin
[DEBUG] Attempting database insert...
[DEBUG] Database result: <APIResponse object>
[DEBUG] Result data: [{'id': 'uuid-here', 'code': '1234', 'created_at': '2024-...'}]
✅ Lock code updated successfully: 1234
ℹ️ No users with active reservations to notify
```

---

## 📧 ¿Qué hacer si nada funciona?

Copia los logs completos de la terminal y compártelos. Incluye:

1. El mensaje de error completo de la UI
2. Los logs [DEBUG] de la terminal
3. El traceback completo si hay una excepción
4. La salida de `SELECT * FROM lock_code LIMIT 5;` desde Supabase

---

## ✅ Checklist de Configuración

- [ ] Archivo `.streamlit/secrets.toml` existe
- [ ] Contiene `[supabase]` con `url` y `key`
- [ ] El `key` es **SERVICE_ROLE** (no anon key)
- [ ] La tabla `lock_code` existe en Supabase
- [ ] La tabla tiene columnas: `id`, `code`, `created_at`
- [ ] La Admin App se conecta exitosamente a Supabase
- [ ] Los logs [DEBUG] aparecen en la terminal

---

## 🎯 Siguiente Paso

**Intenta cambiar la contraseña nuevamente** y copia los logs de la terminal aquí para que podamos diagnosticar exactamente qué está fallando.
