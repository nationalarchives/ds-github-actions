# startup and deployment script for taxonomy .NET framework

$logFile = "\startup.log"
$runFlag = "\startupActive.txt"
$codeTarget = "c://taxonomy-full-index"

function write-log
{
   param(
        [string]$Message,
        [string]$Severity = 'Information'
   )

   $Time = (Get-Date -f g)
   Add-content $logFile -value "$Time - $Severity - $Message"
}

try {
	if (Test-Path -Path "$runFlag" -PathType leaf) {
		write-log -Message "script is already active" -Severity "Warning"
		exit
	} else {
		$Time = (Get-Date -f g)
		Add-content $runFlag -value "$Time - startup script is activated"
	}

	write-log -Message "update code from S3"
	aws s3 cp s3://ds-staging-deployment-source/taxonomy/taxonomy-full-index.zip /temp/taxonomy-full-index.zip

	write-log -Message "write code"
	expand-archive -Path \temp\taxonomy-full-index.zip -DestinationPath \ -force
} catch {
	write-log -Message "Caught an exception:" -Severity "Error"
	write-log -Message "Exception Type: $($_.Exception.GetType().FullName)" -Severity "Error"
	write-log -Message "Exception Message: $($_.Exception.Message)" -Severity "Error"
    exit 1
}
