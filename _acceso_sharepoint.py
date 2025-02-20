import requests
import msal
import webbrowser

# Configuración de la aplicación en Azure
CLIENT_ID = "a88ecf61-6555-4c48-819f-281d06d404e6"  # ID de la aplicación registrada en Azure
TENANT_ID = "59664994-2565-4a5b-af5c-7ea3023a8b8a"  # ID de tu directorio (tenant)
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
REDIRECT_URI = "http://localhost"
SCOPES = ["Files.Read.All"]

# URL de la carpeta compartida en SharePoint
SHAREPOINT_SITE_URL = "https://etles.sharepoint.com/sites/GDETFrenchDesk"
FOLDER_PATH = "/EhTa1x4WbOxOriRvFVwuY-cB7vTzUULsSO8Mbu4PaxC_Fw"

def authenticate_user():
    """Solicita inicio de sesión del usuario y obtiene el token de acceso."""
    app = msal.PublicClientApplication(CLIENT_ID, authority=AUTHORITY)
    flow = app.initiate_device_flow(SCOPES)

    if "message" in flow:
        print("\nInicia sesión en Microsoft en el siguiente enlace:\n")
        print(flow["message"])  # Muestra la URL para iniciar sesión
        webbrowser.open(flow["verification_uri"])  # Abre el navegador automáticamente
    else:
        print("Error al iniciar el flujo de autenticación.")
        return None

    result = app.acquire_token_by_device_flow(flow)
    if "access_token" in result:
        return result["access_token"]
    else:
        print("No se pudo obtener el token de acceso.")
        return None

def get_files_from_sharepoint(access_token):
    """Consulta los archivos de la carpeta en SharePoint."""
    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"https://graph.microsoft.com/v1.0/sites/{SHAREPOINT_SITE_URL}/drive/root:/{FOLDER_PATH}:/children"

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        files = response.json().get("value", [])
        print("\n📂 Archivos en la carpeta de SharePoint:")
        for file in files:
            print(f"- {file['name']}")
    else:
        print("\n❌ Error al obtener archivos:", response.text)

if __name__ == "__main__":
    print("🔑 Iniciando autenticación con Microsoft...")
    token = authenticate_user()

    if token:
        print("\n✅ Autenticación exitosa.")
        get_files_from_sharepoint(token)
    else:
        print("\n❌ No se pudo autenticar al usuario.")
