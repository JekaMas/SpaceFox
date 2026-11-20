import Toybox.Lang;import Toybox.Test;
// Actual current SFR1 owner: 2x2 red RGBA with a copy row.
(:test,:typecheck(false)) function verifiedRocketDecode(logger){
 var bodies=["SFR1:0:2:Af8AAP+B","SFR1:0:2:Av8AAP+B","SFR1:0:2:Af8AAP+BAA=="];
 var pixels="fb3a6a641bbce9b762a240d320a72e963ebbfd6d38cf17e86f37f165574bdbe0";
 for(var i=0;i<5;i+=1){var raw=bodies[i==2?1:(i==3?2:0)];var h=new NativeWireHash();h.put(raw);var digest=h.digest();var store=new PbtMemoryStore();store.write("sf.obj."+digest,raw);var d={"canvas"=>[2,2],"channels"=>4,"pixelSha256"=>i==1?"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa":pixels,"shards"=>[[1,sfrCompactDigest(digest),i==4?h.count+1:h.count]]};if(i!=0){d["__verifyOnly"]=true;}var ok=true;var decoder=new NativeSfrDecoder(store,d);if(i!=0){Test.assertMessage(decoder.bitmap==null&&decoder.dc==null,"verify-only must allocate no drawable");}
  try{var n=0;while(!decoder.step()){n+=1;if(n>=20){throw new Lang.InvalidValueException("decode step bound");}}}catch(e){ok=false;}Test.assertMessage(ok==(i==0),"decode corruption/refusal case "+i);if(i==0){Test.assert(decoder.done&&decoder.bitmap!=null);}
 }
 // Successful verify-only pass must validate the same decoded-pixel digest.
 var raw=bodies[0];var h=new NativeWireHash();h.put(raw);var digest=h.digest();var store=new PbtMemoryStore();store.write("sf.obj."+digest,raw);var d={"canvas"=>[2,2],"channels"=>4,"pixelSha256"=>pixels,"shards"=>[[1,sfrCompactDigest(digest),h.count]],"__verifyOnly"=>true};var decoder=new NativeSfrDecoder(store,d);while(!decoder.step()){}Test.assert(decoder.done&&decoder.bitmap==null&&decoder.dc==null);logger.debug("ROCKET_VERIFY valid_paint_and_verify=true graphics_allocations=0 corrupt_digest_row_length=true");return true;
}
