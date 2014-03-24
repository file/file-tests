Option Explicit
On Error Resume Next
' This script renames a file by appending the current date 
' to the beginning of the file name. Pass the file name as an 
' argument. Pass the long or short file name with a full path! Example:
' start /w DateName.vbs "C:\Program Files\Fnord Web Server\logs\Reference Log.txt"
' Would rename "C:\Program Files\Fnord Web Server\logs\Reference Log.txt"
' to "C:\Program Files\Fnord Web Server\logs\1999-12-28-Reference Log.txt"

'''''''''' Declare variables and objects
Dim strFileName 'As String
Dim strShortName 'As String
Dim strDate 'As String
Dim fs 'As Scripting.FileSystemObject
Dim fol 'As Scripting.Folder
Dim fils 'As Scripting.Files
Dim fil 'As Scripting.File

''''''''''Create the fs object
Set fs = Wscript.CreateObject("Scripting.FileSystemObject")

''''''''''First check the filename argument
If Wscript.Arguments.Count <> 1 Then
	MsgBox "You must pass a path & file name on the command line"
	Wscript.Quit 1
End If
strFileName = Wscript.Arguments(0)
If Not fs.FileExists(strFileName) Then
	MsgBox Wscript.Arguments(0) & " is not a legitimate file name."
	Wscript.Quit 1
End If
Set fil = fs.GetFile(strFileName)
strShortName = fil.ShortName
Set fil = Nothing

''''''''''Now get the date into the format we want
strDate = Year(Now) & "-" & Right("0" & Month(Now),2) & "-" & Right("0" & Day(Now),2) & "-"

''''''''''Find the long file name. Search the directory. Yuk.
Set fol = fs.GetFolder(fs.BuildPath(strFileName, "..\"))
Set fils = fol.Files
For Each fil In fils
	If fil.ShortName = strShortName Then Exit For
Next
If fil.ShortName <> strShortName Then
	MsgBox "Oops -- I can't seem to locate that file"
	Wscript.Quit 1
End If

''''''''''Now warn the user we are about to make a change
'If MsgBox ("This program will rename """ & fil.Name & """ to """ & strDate & fil.Name & """. Continue?", vbOkCancel) = vbCancel Then Wscript.Quit 1

''''''''''Now rename it
fil.Name = strDate & fil.Name
' Use the below code to put date code at end of the file name but before the extension
' If InstrRev(fil.Name, ".") > InstrRev(fil.Name, "\") Then
'	 'The file name has a dot
'	 fil.Name = Left(fil.Name, InstrRev(fil.Name, ".") - 1) & strDate & Mid(fil.Name, InstrRev(fil.Name, "."))
' Else
'	 'The file name has no dot
'	 fil.Name = fil.Name & strDate
' End If

If Err.Number <> 0 Then Wscript.Quit 1

''''''''''Clean up
Set fil = Nothing
Set fol = Nothing
Set fs = Nothing
