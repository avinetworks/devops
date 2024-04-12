# ako-cleanup

## Overview

A Go library to cleanup resources in Avi created by AKO.

## Usage Example

```go
package main

import avicleanupwcp "github.com/avi-cleanup-wcp/clean"
```

```go
cfg := avicleanupwcp.NewAKOCleanupConfig("10.10.25.25", "admin", "",
    "5e3d4ff2ebfec210f9eca84afb9847a3f16e1d8b", "", "abc:12324", false)
err := avicleanupwcp.CleanupAviResources(cfg)
```