import Toybox.Lang;
import Toybox.StringUtil;

(:typecheck(false)) class NativeJsonFrame {
    var kind;var depth;var path;var result;var state=0;var count=0;var previous=null;var keyStart=0;var key=null;var begin=0;
    function initialize(k,d,p,r){kind=k;depth=d;path=p;result=r;}
}

// Resumable current-format parser. No accepted value is published until the
// entire token stream and all existing owner callbacks have completed.
(:extendedCode, :typecheck(false))
class NativeIncrementalJson extends NativeJson {
    var maxInput=0;var stack=[];var result=null;var done=false;var stage=0;var sizeAt=0;var bytes=0;var control=0;
    var token=null;var tokenPurpose=null;var tokenStart=0;var tokenResult="";var tokenSegment=0;var tokenNormalized=false;
    function initialize(){NativeJson.initialize();}
    function dispose(){rowOwner=null;rootOwner=null;nodeOwner=null;source="";stack=null;result=null;}
    function begin(raw,maxBytes){
        if(!(raw instanceof String)||raw.length()>maxBytes){fail();}maxInput=maxBytes;source=raw;index=0;nodes=0;path="";spans={};ignored=[];stack=[];result=null;done=false;stage=0;sizeAt=0;bytes=0;control=0;token=null;hasDel=false;
    }
    // Each call performs at most 16 lexical or grammar operations. A string
    // operation scans at most 128 characters; number scanning is one digit.
    function step(){
        var budget=16;
        while(budget>0&&!done){budget-=1;
            if(stage==0){if(sizeAt<source.length()){var end=sizeAt+64;if(end>source.length()){end=source.length();}bytes+=StringUtil.convertEncodedString(source.substring(sizeAt,end),{:fromRepresentation=>StringUtil.REPRESENTATION_STRING_PLAIN_TEXT,:toRepresentation=>StringUtil.REPRESENTATION_BYTE_ARRAY,:encoding=>StringUtil.CHAR_ENCODING_UTF8}).size();if(bytes>maxInput){fail();}sizeAt=end;continue;}stage=1;continue;}
            if(stage==1){if(control<32){if(!feedMode&&(control==9||control==10||control==13)){control+=1;continue;}var c=control.toChar().toString();if(c.length()>0&&source.find(c)!=null){fail();}control+=1;continue;}hasDel=source.find(127.toChar().toString())!=null;stage=2;continue;}
            if(token!=null){tokenStep();continue;}
            if(stack.size()==0){if(stage==2){stage=3;startValue(0);continue;}white();if(index!=source.length()){fail();}source="";done=true;continue;}
            var f=stack[stack.size()-1];
            if(f.kind.equals("object")){objectStep(f);}else{arrayStep(f);}
        }
        return done;
    }
    function startValue(depth){
        nodes+=1;if(depth>8||nodes>5000){fail();}white();var c=peek();
        if(c.equals("{")){index+=1;stack.add(new NativeJsonFrame("object",depth,path,{}));return;}
        if(c.equals("[")){if(catalogMode&&!path.equals("/unresolved")){fail();}index+=1;stack.add(new NativeJsonFrame("array",depth,path,[]));return;}
        if(c.equals("\"")){startString("value");return;}
        if(c.equals("n")){literal("null");complete(null);return;}if(c.equals("t")){literal("true");complete(true);return;}if(c.equals("f")){literal("false");complete(false);return;}
        token="number";tokenPurpose="value";tokenStart=index;if(c.equals("-")){index+=1;}var first=peek();if(first.equals("0")){index+=1;finishNumber();return;}if(!digit(first)){fail();}
    }
    function objectStep(f){
        if(f.state==0||f.state==5){white();if(f.state==0&&peek().equals("}")){index+=1;stack=stack.slice(0,stack.size()-1);complete(f.result);return;}f.count+=1;if(f.count>4096||!peek().equals("\"")){fail();}f.keyStart=index;f.state=1;startString("key");return;}
        if(f.state==2){white();need(":");path=f.path+"/"+f.key;f.begin=index;f.state=3;startValue(f.depth+1);return;}
        if(f.state==4){white();if(peek().equals("}")){index+=1;stack=stack.slice(0,stack.size()-1);complete(f.result);return;}need(",");f.state=5;return;}
        fail();
    }
    function arrayStep(f){
        if(f.state==0||f.state==5){white();if(f.state==0&&peek().equals("]")){index+=1;stack=stack.slice(0,stack.size()-1);complete(f.result);return;}if(f.result.size()>=4096){fail();}f.state=1;startValue(f.depth+1);return;}
        if(f.state==2){white();if(peek().equals("]")){index+=1;stack=stack.slice(0,stack.size()-1);complete(f.result);return;}need(",");f.state=5;return;}fail();
    }
    function startString(purpose){
        need("\"");token="string";tokenPurpose=purpose;tokenResult="";tokenSegment=index;
        tokenNormalized=feedMode&&(path.find("/launch/")==0||path.find("/upcoming/")==0||path.equals("/dictionaries")||path.equals("/unresolvedCatalogIds"));
    }
    function tokenStep(){
        if(token.equals("number")){if(digit(peek())){index+=1;return;}finishNumber();return;}
        if(index>=source.length()){fail();}
        var end=index+128;if(end>source.length()){end=source.length();}var piece=source.substring(index,end);var quote=piece.find("\"");var slash=piece.find("\\");var stop=piece.length();if(quote!=null&&quote<stop){stop=quote;}if(slash!=null&&slash<stop){stop=slash;}
        if(!feedMode){var prefix=piece.substring(0,stop);if(prefix.find("\n")!=null||prefix.find("\r")!=null||prefix.find("\t")!=null){fail();}}
        if(hasDel&&tokenNormalized&&piece.substring(0,stop).find(127.toChar().toString())!=null){fail();}index+=stop;if(stop==piece.length()){return;}
        if(quote!=null&&stop==quote){var value=tokenResult.length()==0?source.substring(tokenSegment,index):tokenResult+source.substring(tokenSegment,index);index+=1;if(!feedMode&&byteSize(value)>2048){fail();}var purpose=tokenPurpose;token=null;if(purpose.equals("key")){finishKey(value);}else{complete(value);}return;}
        tokenResult+=source.substring(tokenSegment,index);index+=1;var c=peek();index+=1;if(tokenNormalized&&["b","f","n","r","t","u"].indexOf(c)>=0){fail();}
        if(c.equals("\"")||c.equals("\\")||!feedMode&&c.equals("/")){tokenResult+=c;}
        else if(c.equals("b")){tokenResult+=8.toChar().toString();}else if(c.equals("f")){tokenResult+=12.toChar().toString();}else if(c.equals("n")){tokenResult+="\n";}else if(c.equals("r")){tokenResult+="\r";}else if(c.equals("t")){tokenResult+="\t";}
        else if(c.equals("u")){var hexStart=index;var code=hex4();if(feedMode&&(code>=32||code==8||code==9||code==10||code==12||code==13||!source.substring(hexStart,index).equals(source.substring(hexStart,index).toLower()))){fail();}if(code>=0xD800&&code<=0xDBFF){need("\\");need("u");var low=hex4();if(low<0xDC00||low>0xDFFF){fail();}code=0x10000+(code-0xD800)*1024+low-0xDC00;}else if(code>=0xDC00&&code<=0xDFFF){fail();}tokenResult+=code.toChar().toString();}else{fail();}tokenSegment=index;
    }
    function finishNumber(){
        var text=source.substring(tokenStart,index);if(text.equals("-")||feedMode&&text.equals("-0")){fail();}var negative=text.substring(0,1).equals("-");var digits=negative?text.substring(1,text.length()):text;var value=null;
        if(digits.length()>19||digits.length()==19&&digits.compareTo(negative?"9223372036854775808":"9223372036854775807")>0){value=new NativeIntegerLexeme(text);}else{var n=text.toLong();if(n==null){fail();}value=n>= -2147483648l&&n<=2147483647l?n.toNumber():n;}token=null;complete(value);
    }
    function finishKey(key){
        var f=stack[stack.size()-1];if(nodeOwner!=null){nodeOwner.knownField(f.path,key);}if(catalogMode&&f.depth==0&&["schemaVersion","catalogVersion","projection","entries","unresolved","visualSelection"].indexOf(key)<0){fail();}
        if(feedMode){var common=commonKeys.indexOf(key);if(common>=0){key=commonKeys[common];}}
        if(f.result.hasKey(key)||feedMode&&f.previous!=null&&f.previous.compareTo(key)>=0){fail();}f.previous=key;f.key=key;f.state=2;
    }
    function complete(child){
        if(stack.size()==0){result=child;return;}var f=stack[stack.size()-1];
        if(f.kind.equals("array")){if(catalogMode&&!(child instanceof String)){fail();}if(nodeOwner!=null){child=nodeOwner.arrayElement(f.path,f.result.size(),child,f.depth);}f.result.add(child);f.state=2;return;}
        var oldPath=f.path;var key=f.key;var begin=f.begin;var finish=index;
        if(feedMode){
            if(oldPath.equals("")&&["/catalogRevision","/dictionaries","/unresolvedCatalogIds","/launch"].indexOf(path)>=0){spans[path]=[begin,finish];}
            if(path.equals("/launch/ascent_end")||path.equals("/launch/country_code")||path.equals("/launch/site_location_name")){spans[path]=[begin,finish];}
            if(path.equals("/launch/operator_abbrev")){var next=finish;while(next<source.length()&&" \t\r\n".find(source.substring(next,next+1))!=null){next+=1;}if(source.substring(next,next+1).equals(",")){spans[path]=[f.keyStart,next+1];}else{fail();}}
            if(path.equals("/publisher")||path.equals("/launch/source_validated_utc")||path.equals("/launch/stale")||path.equals("/launch/rescheduled")||path.equals("/pollIntervalSeconds")||path.equals("/timingState")){ignored.add([begin,finish]);}child=projection(path,child);
        }
        if(nodeOwner!=null){child=nodeOwner.objectField(oldPath,key,child);}if(rootOwner!=null&&oldPath.equals("")){child=rootOwner.sceneField(key,child);}f.result[key]=child;path=oldPath;f.state=4;
    }
}
