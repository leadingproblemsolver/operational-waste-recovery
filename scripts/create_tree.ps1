
# Relative
Get-ChildItem -Recurse -File | ForEach-Object { Resolve-Path -Relative $_.FullName } | Out-File -FilePath "docs/file_tree.txt" -Encoding utf8


# Absolute
Get-ChildItem -Recurse -File | ForEach-Object { $_.FullName } | Out-File -FilePath "docs/file_tree.txt" -Encoding utf8
