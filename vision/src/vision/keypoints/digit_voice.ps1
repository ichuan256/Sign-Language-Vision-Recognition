param([Parameter(Mandatory=$true)][string]$OutputDirectory)
$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Speech
$digitSynth=New-Object System.Speech.Synthesis.SpeechSynthesizer
try {
    $digitVoice=@($digitSynth.GetInstalledVoices() | Where-Object { $_.Enabled -and $_.VoiceInfo.Culture.Name -like 'zh-*' })
    if($digitVoice.Count -eq 0){throw 'No installed Chinese speech voice'}
    $digitSynth.SelectVoice($digitVoice[0].VoiceInfo.Name)
    $digitSynth.Rate=0
    $digitWords=@([string][char]0x4E00,[string][char]0x4E8C,[string][char]0x4E09,[string][char]0x56DB,[string][char]0x4E94)
    [System.IO.Directory]::CreateDirectory($OutputDirectory) | Out-Null
    for($digitNumber=1;$digitNumber -le 5;$digitNumber++){
        $digitSynth.SetOutputToWaveFile((Join-Path $OutputDirectory ($digitNumber.ToString()+'.wav')))
        $digitSynth.Speak($digitWords[$digitNumber-1])
        $digitSynth.SetOutputToNull()
    }
    @{ready=$true;voice=$digitVoice[0].VoiceInfo.Name;culture=$digitVoice[0].VoiceInfo.Culture.Name} | ConvertTo-Json -Compress
} finally {$digitSynth.Dispose()}
