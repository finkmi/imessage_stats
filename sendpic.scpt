on run {targetPhoneNumber}
	tell application "iMessages"
		set targetService to 1st service whose service type = iMessage
        	set targetBuddy to buddy targetPhoneNumber of targetService
		send POSIX file "/Users/ADMIN/Desktop/photo.png" to targetBuddy
	end tell
end run
