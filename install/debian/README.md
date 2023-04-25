# olympus USB installation

A quick dummy's reminder of how to use this USB installation on Linux.

* Insert USB drive into USB slot

* List disk partitions

```
sudo fdisk -l
```

You're looking for the *Disk* entry that identifies the USB drives. *Disk /dev/sdb* is likely.

Look at the *Device* entries under that disk. One should look obvious due to disk size and type.

Example:

```
Device      Start      End  Sectors  Size Type
/dev/sdb1      40   409639   409600  200M EFI System
/dev/sdb2  411648 15685631 15273984  7.3G Linux filesystem
```

Here the correct device is **/dev/sdb2**.

* Create temporary mount point

```
sudo mkdir /media/olympus
```

Here, *olympus* is used for the directory name, but any other valid name will 
work. Set permissions according to the user(s) you wish to have access.

* Mount the USB drive

In our example:

```
sudo mount /dev/sdb2 /media/olympus
```

Now you can access the USB contents. In our example, to run the networking installation routine:

```
sudo /media/olympus/install/debian/scripts/networking.sh
```

It's good practice to remove the mount point once you're done with it:

```
sudo umount /media/olympus
sudo rmdir /media/olympus
```

