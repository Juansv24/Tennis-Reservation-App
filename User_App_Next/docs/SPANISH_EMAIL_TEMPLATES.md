# Plantillas de Email en Español para Supabase

## Cómo Configurar

1. Ve a tu proyecto en Supabase Dashboard
2. Settings → Auth → Email Templates
3. Edita cada plantilla y reemplaza con el texto en español

---

## 1. Confirm Signup (Verificación de Email)

**Subject:**
```
Confirma tu registro - Reservas de Cancha de Tenis
```

**Body (HTML):**
```html
<h2>¡Bienvenido a Reservas de Cancha de Tenis!</h2>

<p>Gracias por registrarte en nuestro sistema de reservas.</p>

<p>Para completar tu registro y verificar tu correo electrónico, haz clic en el siguiente botón:</p>

<p>
  <a href="{{ .ConfirmationURL }}" style="display: inline-block; padding: 12px 24px; background-color: #2478CC; color: white; text-decoration: none; border-radius: 8px; font-weight: bold;">
    Confirmar mi correo
  </a>
</p>

<p>O copia y pega este enlace en tu navegador:</p>
<p>{{ .ConfirmationURL }}</p>

<p>Si no creaste esta cuenta, puedes ignorar este correo.</p>

<p>¡Nos vemos en la cancha!</p>

<hr>
<p style="color: #666; font-size: 12px;">
  Sistema de Reservas de Cancha de Tenis - Cancha Pública Colina Campestre
</p>
```

---

## 2. Invite User (Invitación)

**Subject:**
```
Has sido invitado - Reservas de Cancha de Tenis
```

**Body (HTML):**
```html
<h2>¡Has sido invitado!</h2>

<p>Has sido invitado a unirte al sistema de Reservas de Cancha de Tenis.</p>

<p>Para aceptar la invitación y crear tu cuenta, haz clic en el siguiente botón:</p>

<p>
  <a href="{{ .ConfirmationURL }}" style="display: inline-block; padding: 12px 24px; background-color: #2478CC; color: white; text-decoration: none; border-radius: 8px; font-weight: bold;">
    Aceptar invitación
  </a>
</p>

<p>O copia y pega este enlace en tu navegador:</p>
<p>{{ .ConfirmationURL }}</p>

<p>¡Nos vemos en la cancha!</p>

<hr>
<p style="color: #666; font-size: 12px;">
  Sistema de Reservas de Cancha de Tenis - Cancha Pública Colina Campestre
</p>
```

---

## 3. Magic Link (Enlace Mágico)

**Subject:**
```
Tu enlace de inicio de sesión
```

**Body (HTML):**
```html
<h2>Inicia sesión en tu cuenta</h2>

<p>Solicitaste un enlace de inicio de sesión para acceder a tu cuenta.</p>

<p>Haz clic en el siguiente botón para iniciar sesión:</p>

<p>
  <a href="{{ .ConfirmationURL }}" style="display: inline-block; padding: 12px 24px; background-color: #2478CC; color: white; text-decoration: none; border-radius: 8px; font-weight: bold;">
    Iniciar sesión
  </a>
</p>

<p>O copia y pega este enlace en tu navegador:</p>
<p>{{ .ConfirmationURL }}</p>

<p>Si no solicitaste este enlace, puedes ignorar este correo.</p>

<hr>
<p style="color: #666; font-size: 12px;">
  Sistema de Reservas de Cancha de Tenis - Cancha Pública Colina Campestre
</p>
```

---

## 4. Change Email Address (Cambio de Email)

**Subject:**
```
Confirma tu nuevo correo electrónico
```

**Body (HTML):**
```html
<h2>Confirma tu nuevo correo</h2>

<p>Solicitaste cambiar tu dirección de correo electrónico.</p>

<p>Para confirmar tu nuevo correo, haz clic en el siguiente botón:</p>

<p>
  <a href="{{ .ConfirmationURL }}" style="display: inline-block; padding: 12px 24px; background-color: #2478CC; color: white; text-decoration: none; border-radius: 8px; font-weight: bold;">
    Confirmar nuevo correo
  </a>
</p>

<p>O copia y pega este enlace en tu navegador:</p>
<p>{{ .ConfirmationURL }}</p>

<p>Si no solicitaste este cambio, contacta al administrador inmediatamente.</p>

<hr>
<p style="color: #666; font-size: 12px;">
  Sistema de Reservas de Cancha de Tenis - Cancha Pública Colina Campestre
</p>
```

---

## 5. Reset Password (Restablecer Contraseña)

**Subject:**
```
Restablece tu contraseña
```

**Body (HTML):**
```html
<h2>Restablece tu contraseña</h2>

<p>Recibimos una solicitud para restablecer tu contraseña.</p>

<p>Para crear una nueva contraseña, haz clic en el siguiente botón:</p>

<p>
  <a href="{{ .ConfirmationURL }}" style="display: inline-block; padding: 12px 24px; background-color: #2478CC; color: white; text-decoration: none; border-radius: 8px; font-weight: bold;">
    Restablecer contraseña
  </a>
</p>

<p>O copia y pega este enlace en tu navegador:</p>
<p>{{ .ConfirmationURL }}</p>

<p>Si no solicitaste restablecer tu contraseña, puedes ignorar este correo de forma segura.</p>

<p><strong>Por seguridad, este enlace expirará en 1 hora.</strong></p>

<hr>
<p style="color: #666; font-size: 12px;">
  Sistema de Reservas de Cancha de Tenis - Cancha Pública Colina Campestre
</p>
```

---

## Instrucciones de Configuración

### Paso 1: Accede a Supabase Dashboard
1. Ve a https://supabase.com
2. Selecciona tu proyecto

### Paso 2: Ve a Email Templates
1. Click en "Settings" (⚙️) en la barra lateral
2. Click en "Auth"
3. Scroll hasta "Email Templates"

### Paso 3: Edita cada plantilla
1. Selecciona el tipo de email (Confirm signup, Reset password, etc.)
2. Reemplaza el Subject con el texto en español
3. Reemplaza el Body con el HTML en español
4. Click "Save"

### Paso 4: Verifica
Repite para las 5 plantillas:
- ✅ Confirm signup
- ✅ Invite user
- ✅ Magic Link
- ✅ Change Email Address
- ✅ Reset Password

---

## Notas Importantes

- Los templates usan variables de Supabase como `{{ .ConfirmationURL }}`
- **NO CAMBIES** estas variables, solo el texto alrededor
- El color azul (`#2478CC`) coincide con el tema de la app
- Todos los enlaces expiran automáticamente por seguridad
