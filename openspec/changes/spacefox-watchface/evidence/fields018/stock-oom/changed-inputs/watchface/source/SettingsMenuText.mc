import Toybox.Lang;
// Menu text mirrors the five existing settings string resources.
(:extendedCode, :typecheck(false)) module SettingsMenuText {
 function fieldsRecent(locale) {if(locale.equals("ru")){return "(недавно)";}if(locale.equals("de")){return "(letzter Wert)";}if(locale.equals("fr")){return "(récent)";}if(locale.equals("es")){return "(reciente)";}return "(recent)";}
 function fieldsCurrent(locale) {if(locale.equals("ru")){return "(текущее)";}if(locale.equals("de")){return "(aktuell)";}if(locale.equals("fr")){return "(actuel)";}if(locale.equals("es")){return "(actual)";}return "(current)";}
 function fieldsNavigation(locale) {
  if(locale.equals("ru")){return ["Другие источники", "Назад", "Далее", "Нет источников"];}
  if(locale.equals("de")){return ["Weitere Quellen", "Zurück", "Weiter", "Keine Quellen"];}
  if(locale.equals("fr")){return ["Autres sources", "Précédent", "Suivant", "Aucune source"];}
  if(locale.equals("es")){return ["Otras fuentes", "Anterior", "Siguiente", "Sin fuentes"];}
  return ["More sources", "Previous", "Next", "No sources"];
 }
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
  if(locale.equals("en")) { return [["Language", "Field 1", "Field 2", "Field 3", "Field 4", "Clock color", "Countdown color", "Field 1 color", "Field 2 color", "Field 3 color", "Field 4 color", "Feed URL", "Launch reminders"], ["English", "Русский", "Deutsch", "Français", "Español", "Automatic"], ["Steps", "Body Battery", "Heart rate", "Stress", "Calories", "Watch battery"], ["Mint", "White", "Ice blue", "Lavender", "Gold", "Pink"]][group]; }
  if(locale.equals("ru")) { return [["Язык", "Поле 1", "Поле 2", "Поле 3", "Поле 4", "Цвет часов", "Цвет отсчёта", "Цвет поля 1", "Цвет поля 2", "Цвет поля 3", "Цвет поля 4", "URL данных", "Сигналы пуска"], ["English", "Русский", "Deutsch", "Français", "Español", "Автоматически"], ["Шаги", "Body Battery", "Пульс", "Стресс", "Калории", "Заряд часов"], ["Мятный", "Белый", "Голубой", "Сиреневый", "Золотой", "Розовый"]][group]; }
  if(locale.equals("de")) { return [["Sprache", "Feld 1", "Feld 2", "Feld 3", "Feld 4", "Uhrfarbe", "Countdown-Farbe", "Farbe Feld 1", "Farbe Feld 2", "Farbe Feld 3", "Farbe Feld 4", "Daten-URL", "Start-Hinweise"], ["English", "Русский", "Deutsch", "Français", "Español", "Automatisch"], ["Schritte", "Body Battery", "Herzfrequenz", "Stress", "Kalorien", "Uhrenakku"], ["Mint", "Weiß", "Hellblau", "Lavendel", "Gold", "Rosa"]][group]; }
  if(locale.equals("fr")) { return [["Langue", "Champ 1", "Champ 2", "Champ 3", "Champ 4", "Couleur heure", "Couleur décompte", "Couleur champ 1", "Couleur champ 2", "Couleur champ 3", "Couleur champ 4", "URL des données", "Alerte lancement"], ["English", "Русский", "Deutsch", "Français", "Español", "Automatique"], ["Pas", "Body Battery", "Fréquence cardiaque", "Stress", "Calories", "Batterie de la montre"], ["Menthe", "Blanc", "Bleu clair", "Lavande", "Or", "Rose"]][group]; }
  if(locale.equals("es")) { return [["Idioma", "Campo 1", "Campo 2", "Campo 3", "Campo 4", "Color de hora", "Color de cuenta", "Color campo 1", "Color campo 2", "Color campo 3", "Color campo 4", "URL de datos", "Avisos de cohete"], ["English", "Русский", "Deutsch", "Français", "Español", "Automático"], ["Pasos", "Body Battery", "Frecuencia cardíaca", "Estrés", "Calorías", "Batería del reloj"], ["Menta", "Blanco", "Azul claro", "Lavanda", "Dorado", "Rosa"]][group]; }
  return values("en",group);
 }
}
