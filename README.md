# misc

## encryptfs
It's was heart breaking if one day we see nothing in the home directory when the ubuntu system got broken.
ok before reinstall it, better to backup our files, though it could be tricky when the file system was encrypted.

So to mount the encrypted file system, one should use the logon password and issue the following command:
> ecryptfs-recover-private .ecryptfs/$USER/.Private
