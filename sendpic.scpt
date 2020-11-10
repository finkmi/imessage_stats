on run {targetPhoneNumber}
	tell application "Messages"
		set targetService to 1st service whose service type = iMessage
        set targetBuddy to buddy targetPhoneNumber of targetService
    	send POSIX file "/Users/michaelfink/pythonProjects/iMessageScripts/wordcloud.png" to targetBuddy
	end tell
end run
