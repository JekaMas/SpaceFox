# Design and evidence boundaries

`NativeDisplayLifecycle` is the owner of hidden, OFF, LOW and ACTIVE presentation permission and transition decisions. The observed OS display mode is authoritative for the mode; callbacks provide lifecycle events and cannot overwrite a newer observed mode. The view interprets transitions as resource, timer and redraw effects. Data, countdown, freshness and reschedule cues are pure presentation inputs and never select a lifecycle state. Background fetch and reminder owners remain separate.

| Event | Independent model input | Expected effect |
| --- | --- | --- |
| show / reopen | visibility and observed OS mode | enter exactly OFF/LOW/ACTIVE; first permitted frame |
| hide | visibility | stop owned work; no paint |
| OFF observation | OS mode | revoke paint, sampling, loader and timers; preserve facts |
| LOW observation | OS mode | enter LOW, invalidate minute once; first AOD frame; cold snapshot once |
| HIGH observation | OS mode | enter ACTIVE and permit normal first frame and post-frame work |
| sleep / wake | callback and observed mode | process current OS state even in duplicate/missing callback order |
| tick | logical UTC minute | at most one unsolicited LOW paint per minute after transition |
| settings / data / late callback | visibility, OS mode | invalidate only when permitted, no hidden/OFF provider work |

Use existing production-view fake ports, independent event model after every event, directed OFF→LOW within one minute and first wake, actual native frame and resource observations, ordinary FR165/M runner. Explicitly record any skip and physical observation limits. Garmin's [FR165 settings](https://www8.garmin.com/manuals/webhelp/GUID-607F08F6-33FC-40BF-9727-84E54043D82D/EN-US/GUID-C9A5E731-8826-4AD0-8087-F6E2EAC625D6.html) separate AOD and timeout; [WatchFace](https://developer.garmin.com/connect-iq/api-docs/Toybox/WatchUi/WatchFace.html) documents HIGH/LOW callbacks and minute LOW updates. Actual callback scheduling and wrist behavior require hardware evidence.
