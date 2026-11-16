import Toybox.Lang;
// Menu text mirrors the five existing settings string resources.
(:extendedCode, :typecheck(false)) module SettingsMenuText {
 function reminderChoices(locale) {
  if(locale.equals("ru")){return ["Выкл.","Вкл."];}
  if(locale.equals("de")){return ["Aus","Ein"];}
  if(locale.equals("fr")){return ["Désactivés","Activés"];}
  if(locale.equals("es")){return ["Desactivados","Activados"];}
  return ["Off","On"];
 }
 function reminderHelp(locale) {
  if(locale.equals("ru")){return "Сон/нет данных: выкл.";}
  if(locale.equals("de")){return "Ruhe/unbekannt: aus";}
  if(locale.equals("fr")){return "Sommeil/inconnu : non";}
  if(locale.equals("es")){return "Sueño/desconocido: no";}
  return "Quiet/unknown: off";
 }
 function rejected(locale) {
  if(locale.equals("ru")){return ["Ошибка данных", "URL / обновить"];}
  if(locale.equals("de")){return ["Daten abgelehnt", "URL / App-Update"];}
  if(locale.equals("fr")){return ["Données refusées", "URL / mise à jour"];}
  if(locale.equals("es")){return ["Datos rechazados", "URL / actualizar"];}
  return ["Feed rejected", "Check URL / update"];
 }
 function values(locale,group) {
  if(locale.equals("en")) {
   if(group==0) { return ["Language", "Field 1", "Field 2", "Field 3", "Field 4", "Clock color", "Countdown color", "Field 1 color", "Field 2 color", "Field 3 color", "Field 4 color", "Feed URL", "Launch reminders"]; }
   if(group==1) { return ["English", "Русский", "Deutsch", "Français", "Español", "Automatic"]; }
   if(group==2) { return ["Steps", "Body Battery", "Heart rate", "Stress", "Calories", "Watch battery"]; }
   if(group==3) { return ["Mint", "White", "Ice blue", "Lavender", "Gold", "Pink"]; }
   return [][group];
  }
  if(locale.equals("ru")) {
   if(group==0) { return ["Язык", "Поле 1", "Поле 2", "Поле 3", "Поле 4", "Цвет часов", "Цвет отсчёта", "Цвет поля 1", "Цвет поля 2", "Цвет поля 3", "Цвет поля 4", "URL данных", "Сигналы пуска"]; }
   if(group==1) { return ["English", "Русский", "Deutsch", "Français", "Español", "Автоматически"]; }
   if(group==2) { return ["Шаги", "Body Battery", "Пульс", "Стресс", "Калории", "Заряд часов"]; }
   if(group==3) { return ["Мятный", "Белый", "Голубой", "Сиреневый", "Золотой", "Розовый"]; }
   return [][group];
  }
  if(locale.equals("de")) {
   if(group==0) { return ["Sprache", "Feld 1", "Feld 2", "Feld 3", "Feld 4", "Uhrfarbe", "Countdown-Farbe", "Farbe Feld 1", "Farbe Feld 2", "Farbe Feld 3", "Farbe Feld 4", "Daten-URL", "Start-Hinweise"]; }
   if(group==1) { return ["English", "Русский", "Deutsch", "Français", "Español", "Automatisch"]; }
   if(group==2) { return ["Schritte", "Body Battery", "Herzfrequenz", "Stress", "Kalorien", "Uhrenakku"]; }
   if(group==3) { return ["Mint", "Weiß", "Hellblau", "Lavendel", "Gold", "Rosa"]; }
   return [][group];
  }
  if(locale.equals("fr")) {
   if(group==0) { return ["Langue", "Champ 1", "Champ 2", "Champ 3", "Champ 4", "Couleur heure", "Couleur décompte", "Couleur champ 1", "Couleur champ 2", "Couleur champ 3", "Couleur champ 4", "URL des données", "Alerte lancement"]; }
   if(group==1) { return ["English", "Русский", "Deutsch", "Français", "Español", "Automatique"]; }
   if(group==2) { return ["Pas", "Body Battery", "Fréquence cardiaque", "Stress", "Calories", "Batterie de la montre"]; }
   if(group==3) { return ["Menthe", "Blanc", "Bleu clair", "Lavande", "Or", "Rose"]; }
   return [][group];
  }
  if(locale.equals("es")) {
   if(group==0) { return ["Idioma", "Campo 1", "Campo 2", "Campo 3", "Campo 4", "Color de hora", "Color de cuenta", "Color campo 1", "Color campo 2", "Color campo 3", "Color campo 4", "URL de datos", "Avisos de cohete"]; }
   if(group==1) { return ["English", "Русский", "Deutsch", "Français", "Español", "Automático"]; }
   if(group==2) { return ["Pasos", "Body Battery", "Frecuencia cardíaca", "Estrés", "Calorías", "Batería del reloj"]; }
   if(group==3) { return ["Menta", "Blanco", "Azul claro", "Lavanda", "Dorado", "Rosa"]; }
   return [][group];
  }
  return values("en",group);
 }
}
