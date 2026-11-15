import Foundation
import CoreText
import CoreGraphics
let url=URL(fileURLWithPath: CommandLine.arguments[1]) as CFURL
let provider=CGDataProvider(url:url)!
let face=CGFont(provider)!
let rows:[(String,String)] = [("Launch reminders","Quiet/unknown: off"),("Сигналы пуска","Сон/нет данных: выкл."),("Start-Hinweise","Ruhe/unbekannt: aus"),("Alerte lancement","Sommeil/inconnu : non"),("Avisos de cohete","Sueño/desconocido: no")]
func width(_ s:String,_ size:CGFloat)->Double {let font=CTFontCreateWithGraphicsFont(face,size,nil,nil);let attr=NSAttributedString(string:s,attributes:[NSAttributedString.Key(kCTFontAttributeName as String):font]);return CTLineGetTypographicBounds(CTLineCreateWithAttributedString(attr),nil,nil,nil)}
for (title,subtitle) in rows {print("\(title)|\(width(title,40))|\(subtitle)|\(width(subtitle,28))")}
