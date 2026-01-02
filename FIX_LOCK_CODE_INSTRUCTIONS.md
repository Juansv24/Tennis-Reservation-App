# 🔧 Instrucciones para Arreglar el Cambio de Contraseña del Candado

## 🎯 El Problema

La tabla `lock_code` **NO tiene permisos de INSERT** configurados en Supabase, mientras que `access_codes` **SÍ los tiene**.

Por eso:
- ✅ Cambiar código de acceso (access_codes) → **FUNCIONA**
- ❌ Cambiar contraseña del candado (lock_code) → **FALLA**

## 📋 Solución (5 minutos)

### Paso 1: Abre Supabase Dashboard

1. Ve a [https://supabase.com](https://supabase.com)
2. Inicia sesión
3. Selecciona tu proyecto **Tennis Reservation App**

### Paso 2: Ejecuta el Script SQL

1. En el menú izquierdo, haz clic en **"SQL Editor"**
2. Haz clic en **"New query"**
3. **Copia y pega** este SQL:

```sql
-- Eliminar políticas antiguas
DROP POLICY IF EXISTS "Authenticated users can view lock code" ON public.lock_code;
DROP POLICY IF EXISTS "Service role can manage lock codes" ON public.lock_code;

-- Crear política nueva (igual que access_codes)
CREATE POLICY "Service role can manage lock codes"
ON public.lock_code
FOR ALL
TO authenticated, anon
USING (true)
WITH CHECK (true);
```

4. Haz clic en **"Run"** (o presiona `Ctrl + Enter`)

### Paso 3: Verifica que Funcionó

En el mismo SQL Editor, ejecuta:

```sql
SELECT
    tablename,
    policyname,
    cmd
FROM pg_policies
WHERE tablename = 'lock_code';
```

**Deberías ver:**
```
tablename  | policyname                         | cmd
-----------+-----------------------------------+-----
lock_code  | Service role can manage lock codes | ALL
```

### Paso 4: Prueba en la Admin App

1. Ve a la **Admin App**
2. Pestaña **"⚙️ Config"**
3. Cambia la contraseña del candado a `1234`
4. Haz clic en **"🔄 Actualizar Contraseña"**

**Ahora debería funcionar!** ✅

---

## 🔍 ¿Por qué pasó esto?

La tabla `lock_code` se creó en el schema inicial con solo permisos de **SELECT**:

```sql
-- Schema inicial (20241205000000_initial_schema.sql)
CREATE POLICY "Authenticated users can view lock code"
  ON public.lock_code FOR SELECT
  USING (auth.uid() IS NOT NULL);
```

Pero la Admin App necesita **INSERT** para agregar nuevas contraseñas.

La tabla `access_codes` ya tenía la política correcta en `complete_rls_policies.sql`, pero ese archivo nunca se ejecutó para `lock_code`.

---

## 📁 Archivo SQL Incluido

También puedes ejecutar el archivo completo:
- **Ubicación:** `User_App_Next/supabase/fix_lock_code_permissions.sql`
- **Cómo usarlo:** Copia todo el contenido y pégalo en Supabase SQL Editor

---

## ✅ Resultado

Después de ejecutar el SQL:

| Tabla | Permisos | Estado |
|---|---|---|
| `access_codes` | SELECT, INSERT, UPDATE, DELETE | ✅ Funciona |
| `lock_code` | SELECT, INSERT, UPDATE, DELETE | ✅ **Arreglado** |

Ahora ambas tablas tienen **exactamente los mismos permisos**.

---

## 🆘 Si Sigue Sin Funcionar

Verifica que estás usando el **SERVICE_ROLE key** en el archivo de secrets de Streamlit:

```bash
cat "Tennis-Reservation-App/Admin App/.streamlit/secrets.toml"
```

Debe contener:
```toml
[supabase]
url = "https://XXXXX.supabase.co"
key = "eyJhbG..." # SERVICE_ROLE key (muy larga, empieza con eyJ)
```

**NO** uses el `anon` key, debe ser el `service_role` key.
