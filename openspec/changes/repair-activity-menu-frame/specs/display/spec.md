## ADDED Requirements

### Requirement: One coherent ACTIVE composition
When mandatory canonical resources are available, every visible ACTIVE frame SHALL use the canonical field icon identities, fonts, and positions for the current settings and facts, including first paint after an OS overlay or restart. Optional art decoding SHALL NOT substitute an alternate ACTIVE layout. A hidden or OFF view SHALL NOT paint. LOW retains its approved layout.

#### Scenario: Return from the system activities menu
- **WHEN** the OS hides and then shows the watch face in ACTIVE
- **THEN** its first and subsequent frames use the same layout, fonts and four configured field icons for equivalent facts and settings, including while optional artwork is pending

#### Scenario: Artwork unavailable or delayed
- **WHEN** optional artwork cannot be loaded within the resource budget
- **THEN** the ACTIVE composition remains intact and only approved map or rocket substitutions are used

#### Scenario: Mandatory resource failure
- **WHEN** a genuine mandatory resource load or paint failure prevents the canonical frame
- **THEN** recovery clears partial composition, preserves clock/date and accepted launch facts, omits all metric values without their identities, and rebuilds the canonical icons/fonts on the next healthy permitted frame
