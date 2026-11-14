// Generated Unicode17 UAX29 compact ranges; see pinned normative fixtures.
import Toybox.WatchUi;import Toybox.StringUtil;
(:extendedCode, :typecheck(false)) module LocaleGraphemes {
 var data=null;
 function load(){if(data==null){var encoded=WatchUi.loadResource(Rez.JsonData.GraphemeProperties);data=StringUtil.convertEncodedString(encoded,{:fromRepresentation=>StringUtil.REPRESENTATION_STRING_BASE64,:toRepresentation=>StringUtil.REPRESENTATION_BYTE_ARRAY});}}
 function contains(offset,count,c){var p=offset;var start=0;for(var i=0;i<count;i+=1){var shift=0;var delta=0;var b=0;do{b=data[p];p+=1;delta|=(b&127)<<shift;shift+=7;}while(b>=128);start+=delta;if(start>c){return false;}shift=0;var length=0;do{b=data[p];p+=1;length|=(b&127)<<shift;shift+=7;}while(b>=128);if(c<=start+length){return true;}}return false;}
 function incbExtend(c){return c==0x200d||(extend(c)&&c!=0x200c&&!incbLinker(c));}
 function extend(c){return contains(0,384,c);}
 function spacing(c){return contains(827,158,c);}
 function prepend(c){return contains(1172,15,c);}
 function control(c){return contains(1214,17,c);}
 function pictographic(c){return contains(1263,156,c);}
 function incbConsonant(c){return contains(1599,76,c);}
 function incbLinker(c){return contains(1769,20,c);} function hangul(a,b){var al=(a>=0x1100&&a<=0x115f)||(a>=0xa960&&a<=0xa97c);var bl=(b>=0x1100&&b<=0x115f)||(b>=0xa960&&b<=0xa97c);var av=(a>=0x1160&&a<=0x11a7)||(a>=0xd7b0&&a<=0xd7c6);var bv=(b>=0x1160&&b<=0x11a7)||(b>=0xd7b0&&b<=0xd7c6);var at=(a>=0x11a8&&a<=0x11ff)||(a>=0xd7cb&&a<=0xd7fb);var bt=(b>=0x11a8&&b<=0x11ff)||(b>=0xd7cb&&b<=0xd7fb);var asyl=a>=0xac00&&a<=0xd7a3;var bsyl=b>=0xac00&&b<=0xd7a3;return al&&(bl||bv||bsyl)||(av||asyl&&(a-0xac00)%28==0)&&(bv||bt)||(at||asyl&&(a-0xac00)%28!=0)&&bt;}
}
