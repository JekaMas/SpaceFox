import Toybox.Lang;
// Schedule, source precision and presentation were projected by the publisher.
(:extendedCode,:typecheck(false))
function feedScene(packet,now){
    if(packet==null||packet.presentation==null){return null;}
    packet.advance(now);packet.presentation.stale=packet.stale;packet.presentation.rescheduled=packet.rescheduled;return packet.presentation;
}
