' Lance ARIA comme une application : pas de fenetre noire.
'
' Le .bat reste le moteur (il verifie Ollama, met a jour, demarre le serveur),
' mais sa sortie part dans demarrage.log au lieu de s'afficher. Si la page ne
' s'ouvre pas, c'est ce fichier qu'il faut lire.
'
' ARIA_SILENT=1 dit au .bat de ne jamais faire "pause" : un processus cache
' bloque sur une touche ne se termine plus jamais.

Set sh  = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
here = fso.GetParentFolderName(WScript.ScriptFullName)

sh.Environment("PROCESS")("ARIA_SILENT") = "1"
sh.Environment("PROCESS")("ARIA_NO_BROWSER") = "1"
sh.CurrentDirectory = here

cmd = "cmd /c """ & here & "\run_local.bat"" > """ & here & "\demarrage.log"" 2>&1"
sh.Run cmd, 0, False

' On attend que le serveur reponde avant d'ouvrir la page : sinon le
' navigateur affiche une erreur de connexion et il faut recharger a la main.
Set http = CreateObject("MSXML2.ServerXMLHTTP.6.0")
For i = 1 To 90
  WScript.Sleep 1000
  On Error Resume Next
  http.Open "GET", "http://127.0.0.1:8000/health", False
  http.setTimeouts 1000, 1000, 1000, 2000
  http.Send
  If Err.Number = 0 Then
    On Error GoTo 0
    sh.Run "http://127.0.0.1:8000", 1, False
    WScript.Quit
  End If
  Err.Clear
  On Error GoTo 0
Next

MsgBox "ARIA n'a pas demarre en 90 secondes." & vbCrLf & vbCrLf & _
       "Ouvre demarrage.log dans le dossier d'ARIA pour voir pourquoi.", _
       48, "ARIA"
