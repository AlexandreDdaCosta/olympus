# olympus networking hardware

These directories contain needed files and specifications for the networking
hardware supported by this specific installation.

Each hardware directory may include the following:

## adapter.conf

Identification and installation details for the hardware.

### **HARDWARE_MODEL**. Formal identifier.
### **HARDWARE_NAME**. Descriptive string.

## README.md

Useful installation documentation and commentary. Build instructions
for modules.

## /modules directory with required pre-built kernel files (extension .ko)

Drivers specific to the hardware. 

## Dependencies

Listing of deb dependencies, of which each line has the following format:

```
<Package name> <Deb file name>
```

When packages depend on other packages, order the deepest dependency before
the others.
