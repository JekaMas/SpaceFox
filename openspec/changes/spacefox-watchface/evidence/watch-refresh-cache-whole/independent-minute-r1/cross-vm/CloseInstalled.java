// Ask the SDK device channel to close only the specified installed app; no push.
import com.garmin.monkeybrains.monkeydodeux.MonkeyDoDeux;
import com.garmin.connectiq.common.communication.shell.ShellProcess;
import com.garmin.connectiq.common.communication.shell.ShellUtils;
import com.garmin.connectiq.common.communication.channels.platform.PlatformChannel;
import com.garmin.connectiq.common.communication.channels.device.DeviceChannel;
import com.garmin.connectiq.common.communication.channels.device.IDeviceChannelListener;
import java.io.File;
import java.lang.reflect.Field;
import java.util.UUID;
public final class CloseInstalled {
 private static class Observer extends MonkeyDoDeux {
  @Override public void appTerminated(UUID uuid,IDeviceChannelListener.AppInfo info){System.out.println("SDK_APP_TERMINATED uuid="+uuid+" background="+(info!=null&&info.isBackgroundApp()));super.appTerminated(uuid,info);}
 }
 private static Object get(Object obj,String name) throws Exception {Field f=MonkeyDoDeux.class.getDeclaredField(name);f.setAccessible(true);return f.get(obj);}
 private static void set(Object obj,String name,Object value) throws Exception {Field f=MonkeyDoDeux.class.getDeclaredField(name);f.setAccessible(true);f.set(obj,value);}
 public static void main(String[] args) throws Exception {
  UUID uuid=UUID.fromString(args[0]);File shellPath=new File(args[1]);Observer app=new Observer();set(app,"mUuid",uuid);
  ShellProcess shell=(ShellProcess)get(app,"mShell");PlatformChannel platform=(PlatformChannel)get(app,"mPlatformChannel");DeviceChannel device=(DeviceChannel)get(app,"mDeviceChannel");
  int port=ShellUtils.findSimulatorPort(shellPath);if(port<0)throw new IllegalStateException("no private simulator");String[] cmd=ShellUtils.getShellCommand(shellPath,port).toArray(new String[0]);shell.start(Runtime.getRuntime().exec(cmd));shell.sendMessage("ciq");
  System.out.println("CLOSE_INSTALLED uuid="+uuid+" push=false port="+port);platform.openDevice("fr165");device.closeApp(uuid);Thread.sleep(5000);shell.stop();shell.waitForThreads();System.out.println("CLOSE_INSTALLED_END push=false");
 }
}
