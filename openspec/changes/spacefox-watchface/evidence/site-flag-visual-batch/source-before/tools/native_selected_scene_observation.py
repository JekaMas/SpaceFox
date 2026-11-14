#!/usr/bin/env python3
"""Observe actual current CDN FeedService and cache/scene, without seed bytes.

The expected artifact supplies assertions only. It is never inserted into the VM.
Caller owns the exclusive simulator lease, export and cleanup UI actions.
"""
import argparse
import json
from pathlib import Path
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.native_full_visual_runtime import (
    GROUPS,
    IMPORTS,
    build_probe,
    literal,
    observer_source,
)


def source(identity, feed, reopen=False):
    launch = feed["launch"]
    site = launch.get("site_location_name") or launch.get("site_name") or ""
    country = launch.get("country_code") or launch.get("country_name") or ""
    site = country + " · " + site if country and site else country or site
    return (
        IMPORTS
        + """
(:typecheck(false)) class SelectedProxy extends WatchUi.WatchFace {
 var app;function initialize(a){WatchFace.initialize();app=a;}
 function onLayout(dc){app.view.onLayout(dc);}function onShow(){app.view.onShow();}function onHide(){app.view.onHide();}
 function onUpdate(dc){var v=app.view;var reads=app.feed.store.reads;var writes=app.feed.store.writes;v.onUpdate(dc);if(reads!=app.feed.store.reads||writes!=app.feed.store.writes){throw new Lang.InvalidValueException("redraw storage I/O");}app.inspect();}
}
(:background,:typecheck(false)) class SfrRuntimeApp extends SpaceFoxApp {
 var complete=false;var callbacks=0;
 function initialize(){SpaceFoxApp.initialize();NativeMetrics.enabled=true;}
 """
        + (
            "function getServiceDelegate(){return [new SelectedQuiet()];}"
            if reopen
            else ""
        )
        + """
 (:typecheck(disableBackgroundCheck)) function getInitialView(){Application.Properties.setValue("FeedBaseUrl","""
        + literal(identity["url"])
        + """);Application.Properties.setValue("Language",0);SpaceFoxApp.getInitialView();"""
        + ("Background.deleteTemporalEvent();" if reopen else "")
        + """return [new SelectedProxy(self)];}
 (:typecheck(disableBackgroundCheck)) function onBackgroundData(data as Application.PersistableType) as Void {callbacks+=1;SpaceFoxApp.onBackgroundData(data);}
 function ensure(ok,message){if(!ok){throw new Lang.InvalidValueException("SELECTED_SCENE "+message);}}
 (:typecheck(disableBackgroundCheck)) function inspect(){if(complete||view.downloaded==null||view.sfrBuild!=null||view.sfrRequested){return;}var r=view.downloaded;ensure(r instanceof NativeSfrRenderer,"wrong renderer");
 ensure(System.getSystemStats().totalMemory==126784,"not ordinary heap");
 ensure(feed.packet.wireHash.equals("""
        + literal(
            __import__("hashlib")
            .sha256(
                json.dumps(
                    feed, sort_keys=True, ensure_ascii=False, separators=(",", ":")
                ).encode()
            )
            .hexdigest()
        )
        + """),"public feed advanced or bytes mismatch; recapture before asserting");
 ensure(feed.packet.launchId().equals("""
        + literal(launch["launch_id"])
        + """),"selected launch mismatch");
 ensure(view.context.rocket.equals("""
        + literal(launch["configuration_name"])
        + """)&&view.context.operator.equals("""
        + literal(launch["operator_name"])
        + """)&&view.context.purpose.equals("""
        + literal(launch["mission_purpose"])
        + """)&&view.context.site.equals("""
        + literal(site)
        + """),"context association mismatch");
 ensure(r.selectionHash.equals("""
        + literal(feed["visualSelection"]["sha256"])
        + """),"source selection mismatch");
 ensure(r.scene["position"]!=null&&r.mapBitmap!=null&&r.bitmap!=null&&r.modelOriginBitmap!=null&&r.operatorBitmap!=null,"selected map/model/marks missing");
 var seal=feed.store.read("sf.commit")["seal"];var active=feed.store.read("sf.raster.active");ensure(active["base"].equals(configuredFeedUrl())&&active["selectionHash"].equals(r.selectionHash),"persistent cache coherence");
 var snapshot=view.snapshot();System.println("SELECTED_SCENE_COMPLETE mode="""
        + ("reopen" if reopen else "public-background")
        + """ callbacks="+callbacks+" generation="+feed.packet.document["publisher"]["generation"]+" sourceEpoch="+feed.packet.validation+" acceptedRawSha256="+feed.packet.wireHash+" selection="+r.selectionHash+" acceptedSeal="+seal+" rocket="+view.context.rocket+" operator="+view.context.operator+" purpose="+view.context.purpose+" site="+view.context.site+" position="+r.scene["position"]+" countdown="+view.presentation.countdown(snapshot,true)+" stale="+feed.packet.stale+" rescheduled="+feed.packet.rescheduled+" ordinaryBytes="+System.getSystemStats().totalMemory+" usedBytes="+System.getSystemStats().usedMemory+" mapBitmap=true rocketBitmap=true modelOrigin=true operatorMark=true markerAnchor=335,165 noDrawIo=true owner="+NativeMetrics.ownerTag);complete=true;}
}
"""
        + (
            "(:background,:typecheck(false)) class SelectedQuiet extends FeedService {function onTemporalEvent(){Background.deleteTemporalEvent();Background.exit(null);}}"
            if reopen
            else ""
        )
    )


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=["public", "reopen", "cleanup"])
    p.add_argument("--identity", type=Path, required=True)
    p.add_argument("--feed", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    identity = json.loads(a.identity.read_text())
    feed = json.loads(a.feed.read_text())
    GROUPS["selected-scene"] = (identity["uuid"], identity["basename"])
    raw = (
        observer_source(identity["url"], cleanup=True)
        if a.mode == "cleanup"
        else source(identity, feed, a.mode == "reopen")
    )
    result = build_probe(a.output, raw, group="selected-scene")
    print(
        json.dumps(
            {key: result[key] for key in ("exitCode", "packageName", "packageSha256")}
        )
    )
    return result["exitCode"]


if __name__ == "__main__":
    sys.exit(main())
