# PowerShell script to list the 50 biggest files in the OS
# This script uses Get-ChildItem with depth and sorts by size

Get-ChildItem -Path "C:\" -Recurse -File -ErrorAction SilentlyContinue | 
    Sort-Object Length -Descending | 
    Select-Object -First 50 | 
    Format-Table -AutoSize @{Name='Size (GB)'; Expression={"{0:F2}" -f ($_.Length / 1GB)}}, 
                        @{Name='Full Path'; Expression={$_.FullName}}, 
                        @{Name='Name'; Expression={$_.Name}} -Wrap