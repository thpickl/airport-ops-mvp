# Digital Twin Guide

The portable package contains 15 DTDL v2 interfaces, one compact instance of each interface, valid relationships, mapping documentation, and optional deployment notebook `14_Deploy_Digital_Twin`.

Models cover Airport, Terminal, Zone, Checkpoint, Gate, Stand, AircraftType, Flight, Queue, BaggageAsset, Asset, MaintenanceAsset, EnergyMeter, MaintenanceWorkOrder, and Incident. Operational/facility twin IDs begin with `SYN-`. The airport twin holds only the public CDG identity anchor and is not an operational representation.

The core graph is descriptive and platform neutral. The Azure Digital Twins adapter is disabled until a runtime endpoint, authentication, and explicit apply mode are supplied. Model version collisions fail rather than overwrite an immutable definition. No twin relationship enables a control command.