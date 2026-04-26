import json
from db_config import get_connection, save_entity

TERRAIN_DATA = {
    'Grasland': {
        'id': 1, 'startgebiet': True, 'regen_pct': 30,
        'aufwertungen': [], 'abwertungen': [],
        'beschreibung': 'Saftige, weite, grüne Wiesen machen das Grasland aus. Kein Wunder also, dass hier viele Tierarten gezüchtet werden können. Doch nicht nur Tiere grasen hier genüsslich, der Boden eignet sich auch hervorragend für den Anbau einer Vielzahl von Nahrungsmitteln oder zum Bau edler Plantagen. Nicht oft, aber immer wieder kommt es vor, dass Kies oder Braunkohle gefunden wird.',
        'gebaeude': {'Kartoffelfarm': 100, 'Imkerei': 100, 'Apfelplantage': 100, 'Holzfäller': 75, 'kleine Getreidefarm': 100, 'Auffangbecken': 30, 'Hühnerfarm': 100, 'Flachsplantage': 100, 'Sägegrube': 50},
    },
    'Steppe': {
        'id': 2, 'startgebiet': True, 'regen_pct': 25,
        'aufwertungen': [], 'abwertungen': [],
        'beschreibung': 'Selten benetzt üppiger Regen den trockenen Steppenboden, doch sind Tiere genügsam. So ziehen große Tierherden über die Steppe und ernähren sich von dem gelben, trockenen Gras. Wenige Pflanzen gedeihen nutzbringend auf dem Boden, doch der, der sich auskennt, kann sich wohl ernähren. Oft beherbergt die karge Erde jedoch wertvolle Schätze wie Kies, Lehm oder Ton. Auch kann ab und an Braunkohle und Salpeter gefunden werden.',
        'gebaeude': {'Kartoffelfarm': 100, 'Holzfäller': 50, 'kleine Getreidefarm': 100, 'Auffangbecken': 25, 'Tongrube': 80, 'Lehmgrube': 90, 'Hühnerfarm': 100, 'Flachsplantage': 100, 'Feldbrandziegelei': 100},
    },
    'Ödland': {
        'id': 3, 'startgebiet': False, 'regen_pct': 6,
        'aufwertungen': ['Steppe'], 'abwertungen': ['Wüste'],
        'beschreibung': 'So gut wie nie lässt eine Regenwolke hier ihr kostbares Gut fallen. Zwischen den wenigen Pflanzen, die der Umwelt trotzen, leben in Höhlen und unter Steinen, die gefürchteten roten Scorpione. Das Ödland ist führwahr kein angenehmer, doch ein gefährlicher Ort zum Leben. Große Mengen Lehm können jedoch aus dem Boden gewonnen werden und immer wieder findet sich auch Kies und Sand. Seltener stößt man auf Ton, Braunkohle oder Salpeter. Wenn man tief genug gräbt, hat man sogar die Chance, Erdöl zu finden.',
        'gebaeude': {'Kartoffelfarm': 50, 'Auffangbecken': 10, 'Feldbrandziegelei': 100},
    },
    'Wald': {
        'id': 4, 'startgebiet': True, 'regen_pct': 45,
        'aufwertungen': [], 'abwertungen': [],
        'beschreibung': 'Das dichte Buschwerk und die mächtigen Bäume des Waldes eigenen sich hervorragend zum Bau großer Gebäude. Außerdem findet man auf einem Streifzug so manche Leckerei. Hungern wird man nicht im Wald, doch sollte man sich vor den Spinnen hüten, die ihre feinen Netze zwischen den Bäumen spannen.',
        'gebaeude': {'Imkerei': 100, 'Apfelplantage': 100, 'Holzfäller': 100, 'Kräutergarten': 100, 'Auffangbecken': 50, 'Nuggretzucht': 100, 'Sägegrube': 100},
    },
    'Grasfelsland': {
        'id': 5, 'startgebiet': True, 'regen_pct': 30,
        'aufwertungen': [], 'abwertungen': [],
        'beschreibung': 'Weite Wiesen, die hin und wieder von felsigen Landstrichen unterbrochen werden, machen das Wesen dieser Landschaft aus. Das Grasfelsland ist gut geeignet zur Zucht von Tieren und auch Nahrungsmittel und Wasser sind hier, wenn auch nicht üppig, zur Genüge vorhanden. Vor allem bietet sich aber die Möglichkeit Steine zu gewinnen die zum Bau größeren Gebäude als einfachen Holzhütten benötigt werden. Dieses Terrain bietet recht gute Chancen Kies zu finden, gelegentlich findet man Braunkohle und sehr selten kann auch Erdöl gefunden werden.',
        'gebaeude': {'Kartoffelfarm': 50, 'Imkerei': 100, 'Apfelplantage': 75, 'Holzfäller': 75, 'Steinmetz': 100, 'kleine Getreidefarm': 50, 'Kiesgrube': 100, 'Auffangbecken': 30, 'Hühnerfarm': 100, 'Sägegrube': 50},
    },
    'Sumpfland': {
        'id': 6, 'startgebiet': True, 'regen_pct': 55,
        'aufwertungen': [], 'abwertungen': [],
        'beschreibung': 'Sümpfe sind stark bewachsene und sehr feuchte Gebiete. Das Wasser, das man aus diesen Gebieten erhält reicht problemlos, eine zweite Provinz mit zu versorgen. Aufgrund des sehr feuchten und dadurch weichen Bodens ist es unmöglich nach Bodenschätzen wie Erzen, Erdöl oder ähnlichem zu suchen. Dies wird jedoch durch die Möglichkeiten zum Abbau von Holz und dem Anbau verschiedenster Nahrungsmittel und anderer Güter für das Volk mehr als ausgeglichen.',
        'gebaeude': {'Sojafarm': 100, 'Holzfäller': 100, 'Hanfplantage': 100, 'Kräutergarten': 100, 'Auffangbecken': 50, 'Nuggretzucht': 100, 'Sägegrube': 100, 'Reisfarm': 100},
    },
    'Grashügel': {
        'id': 7, 'startgebiet': True, 'regen_pct': 35,
        'aufwertungen': [], 'abwertungen': [],
        'beschreibung': 'Saftiges Gras erstreckt sich so weit das Auge reicht über eine von Hügeln durchwachsene Landschaft. Wie jede Art der Graslandschaft bietet auch der Grashügel optimale Bedingungen für die Tierzucht, auch Wasser kann man hier ausreichend finden. Aufgrund der vielen Hügel hat dieses Landschaft allerdings einen kleinen Nachteil in der Produktivität von Plantagen gegenüber dem Grasland. Man hat gute Chancen, in diesem Terrain Braunkohle zu finden, aber auch Lehm und Kalkstein kann von Zeit zu Zeit gefunden werden. Seltener trifft man auf Salpeter- und Diamantenvorkommen.',
        'gebaeude': {'Kartoffelfarm': 50, 'Imkerei': 100, 'Apfelplantage': 75, 'Holzfäller': 75, 'Auffangbecken': 35, 'Hühnerfarm': 100, 'Flachsplantage': 100, 'Sägegrube': 50},
    },
    'Grasgebirge': {
        'id': 8, 'startgebiet': False, 'regen_pct': 40,
        'aufwertungen': [], 'abwertungen': [],
        'beschreibung': 'Zu dieser Terrainart gehören Landschaftsstriche, die von Gebirgen geprägt sind, jedoch auch Grasflächen aufweisen. Im Gegensatz zu anderen grasbewachsenen Landschaften eignet sich das Grasgebirge jedoch nicht zur Viehzucht. Dafür kann man hier nahezu alle Bodenschätze mit einer akzeptablen Wahrscheinlichkeit finden und die Wasserversorgung ist durch die häufigen Regengüsse im Gebirge ausgezeichnet.',
        'gebaeude': {'Apfelplantage': 50, 'Steinmetz': 100, 'Auffangbecken': 40, 'Sägegrube': 50},
    },
    'Eiswüste': {
        'id': 9, 'startgebiet': False, 'regen_pct': 40,
        'aufwertungen': [], 'abwertungen': [],
        'beschreibung': 'Die Eiswüste ist eine absolut gnadenlose, eiskalte und einsame Einöde. Das einzige, wofür es sich lohnt, dieses Gebiet zu besiedeln ist die relativ gute Chance, Erdöl und andere Vorkommen zu finden. Achtung. Provinzausbau ist auf Camp beschränkt und die meisten Land- und Stadtgebäude sind in der Eiswüste nicht baubar.',
        'gebaeude': {'Auffangbecken': 40},
    },
    'Wüste': {
        'id': 10, 'startgebiet': False, 'regen_pct': 10,
        'aufwertungen': [], 'abwertungen': [],
        'beschreibung': 'Eine sehr unwirtliche und sehr harte Gegend. In einer Wüste ohne Hilfe von außen zu überleben ist unglaublich schwierig. Die Wüste bietet kaum Wasser, größere Menschenmengen lassen sich kaum mit Wasser allein aus der Wüste versorgen. Dafür kann man in der Wüste garantiert Sand finden. Oft findet man auch Erdöl und/oder Salz, gelegentlich Salpeter und selten auch Diamanten.',
        'gebaeude': {'Auffangbecken': 10, 'Feldbrandziegelei': 100},
    },
    'Tropensumpf': {
        'id': 11, 'startgebiet': True, 'regen_pct': 60,
        'aufwertungen': [], 'abwertungen': [],
        'beschreibung': 'Sumpfiger Boden und tropische Hitze machen dieses Terrain aus. Wegen dem feuchten Boden ist die Luft nicht einfach nur heiß, was noch einigermaßen erträglich wäre, sondern hat dazu noch eine sehr hohe Luftfeuchtigkeit. In dieser schwülen Luft zu leben fällt nicht jedem leicht. Aufgrund des sumpfigen, matschigen Bodens ist es unmöglich nach irgendwelchen Vorkommen - abgesehen vom offensichtlich vorhandenen Wasser - zu suchen. Auch der Anbau von Nahrungsmitteln ist sehr aufwändig und ist dem entsprechend erst nach einigen grundlegenden Technischen Fortschritten möglich. Die hier abbaubaren Bauhölzer, Edelhölzer und andere wertvolle Güter, sind jedoch ein willkommenes Tauschgut bei vielen Provinzbesitzern mit einer besseren Nahrungsmittelversorgung.',
        'gebaeude': {'Palmenplantage': 75, 'Kräutergarten': 100, 'Wollspinnenzucht': 100, 'Auffangbecken': 30, 'Nuggretzucht': 100, 'Kautschukplantage': 100, 'Teehain': 100, 'Sägegrube': 100, 'Tropenholzfäller': 100, 'Reisfarm': 100},
    },
    'Dschungel': {
        'id': 12, 'startgebiet': True, 'regen_pct': 50,
        'aufwertungen': [], 'abwertungen': [],
        'beschreibung': 'Wer kennt sie nicht, die Geschichten von wilden Tieren und einer Pflanzenwelt die ohne jegliche Ordnung wächst, wie es ihr gefällt? Manche dieser Geschichten sind war, andere nicht. Tatsache ist jedoch, dass der Dschungel wie jedes andere Gelände auch Herausforderungen birgt. Wer hier Fuss gefasst hat, wird weder Hunger leiden, noch im freien schlafen müssen. Der Dschungel bietet genügend Nahrungsmittel, Bau- und Edelholz, sowie Produkte wertvoller Plantagen um sich zu versorgen und Handelspartner in aller Welt finden zu können.',
        'gebaeude': {'Palmenplantage': 100, 'Wollspinnenzucht': 100, 'Auffangbecken': 50, 'Nuggretzucht': 100, 'Kautschukplantage': 100, 'Sägegrube': 100, 'Tropenholzfäller': 100, 'Bananenhain': 100},
    },
    'Sanddünen': {
        'id': 13, 'startgebiet': False, 'regen_pct': 10,
        'aufwertungen': [], 'abwertungen': [],
        'beschreibung': 'Ein Gelände ähnlich wie eine Wüste. Der Unterschied besteht darin, dass der Sand auf diesem Gelände sich vom Wind zu kleinen Bergen auftürmen lässt. In den Sanddünen kann man garantiert Sand finden, manchmal auch Salz und selten Diamanten.',
        'gebaeude': {'Auffangbecken': 2, 'Feldbrandziegelei': 100},
    },
    'Felsgebirge': {
        'id': 14, 'startgebiet': False, 'regen_pct': 15,
        'aufwertungen': [], 'abwertungen': [],
        'beschreibung': 'Karge und trockene Landschaftszüge machen das Wesen des Felsgebirges aus. Es gibt hier selten Regen und eine autonome Wasserversorgung ist kaum möglich. Dafür kann man in Felsgebirgen nach einer großen Zahl verschiedenster Ressourcen suchen, wovon man sicher den ein oder anderen finden und abbauen kann.',
        'gebaeude': {'Steinmetz': 100, 'Auffangbecken': 10, 'Feldbrandziegelei': 100},
    },
    'Ödhügel': {
        'id': 15, 'startgebiet': False, 'regen_pct': 9,
        'aufwertungen': ['Stepphügel'], 'abwertungen': ['Sanddünen'],
        'beschreibung': 'Ödhügel sind sehr einsame und einseitige Landschaften, in denen man kaum flache, waagrechte Gebiete findet. Sie bieten zwar Möglichkeit zur Landwirtschaft, doch ist deren Effektivität zu vernachlässigen. Auch die Wasserversorgung kann sich ohne Hilfe von außen manchmal als schwierig erweisen. Solche kargen Landschaften wie Ödhügel eignen sich eher zum Abbau verschiedenster Rohstoffe. Für Ressourcen wie Lehm, Braunkohle und Sand bestehen gute bis sehr gute Chancen auf einen Fund, Kalkstein, Salz, Salpeter und selten auch Diamanten sind jedoch auch zu finden.',
        'gebaeude': {'Kartoffelfarm': 25, 'Auffangbecken': 9, 'Feldbrandziegelei': 100},
    },
    'Ödgebirge': {
        'id': 16, 'startgebiet': False, 'regen_pct': 20,
        'aufwertungen': [], 'abwertungen': [],
        'beschreibung': 'Die Attribute öde und gebirgig bezeichnen dieses Terrain am besten. Beinahe keine Nahrungsmittel lassen sich auf dem kargen und steinigen Boden kultivieren, aber es mag einem sehr wohl gelingen, ein paar der berüchtigten Bluescorpions zu fangen, die hier ihr Jagdrevier haben. Durch die Zucht derselben kann man die Nahrungskette im Ödgebirge teilweise herumdrehen. Die eigentliche Stärke dieser Gebiete liegt aber in ihren Vorkommen an Bodenschätzen und Steinen, die sich in Steinbrüchen brechen und abtransportieren lassen.',
        'gebaeude': {'Steinmetz': 100, 'Auffangbecken': 10, 'Feldbrandziegelei': 100},
    },
    'Stepphügel': {
        'id': 17, 'startgebiet': True, 'regen_pct': 28,
        'aufwertungen': [], 'abwertungen': [],
        'beschreibung': 'Der Stepphügel ist im Endeffekt lediglich ein etwas besserer Ödhügel. Beide Terrains unterscheiden sich dem Aussehen nach im Groben lediglich um ein wenig Gras. Wirtschaftlich hat dies jedoch weitreichendere Folgen, als es vielleicht auf den ersten Blick ersichtlich ist. Aufgrund der - wenn auch trockenen und mageren - Grasdecke besteht in Stepphügeln die Möglichkeit auf eine recht ausgedehnte Tierzucht. Auch die Wasserversorgung erweist sich hier als besser, als die magere Grasdecke erscheinen lässt. Eines hat der Stepphügel jedoch mit dem Ödhügel gemeinsam: In diesem Terrain besteht ebenfalls die Chance auf eine Vielzahl verschiedenster Ressourcen, die nur darauf warten, gefunden zu werden.',
        'gebaeude': {'Kartoffelfarm': 75, 'Holzfäller': 50, 'kleine Getreidefarm': 75, 'Auffangbecken': 28, 'Tongrube': 50, 'Lehmgrube': 75, 'Hühnerfarm': 100, 'Flachsplantage': 100, 'Feldbrandziegelei': 100},
    },
    'Steppgebirge': {
        'id': 18, 'startgebiet': False, 'regen_pct': 33,
        'aufwertungen': [], 'abwertungen': [],
        'beschreibung': 'Das Steppgebirge ist ein weiteres der zahlreichen kargeren Terrains. In der Landwirtschaft kann man eine Hand voll Kartoffeln als das höchste der Gefühle bezeichnen, doch für die Versorgung eines größeren Volkes reicht der Ertrag eines Steppgebirges einfach nicht aus. Wasser dagegen wird man hier ausreichend finden können. Betrachtet man jedoch den Bergbau, so wird man feststellen, dass das Steppgebirge ein sehr ertragreiches Terrain ist. Man kann hier jeglich Art von Metallerz finden, aber auch Ton, Bauxit, Kalkstein, Schwefel, Salpeter und Diamanten.',
        'gebaeude': {'Kartoffelfarm': 25, 'Steinmetz': 100, 'Auffangbecken': 30, 'Feldbrandziegelei': 100},
    },
    'Ödfelsland': {
        'id': 19, 'startgebiet': False, 'regen_pct': 6,
        'aufwertungen': ['Steppfelsland'], 'abwertungen': ['Wüste'],
        'beschreibung': 'Wie bei allen Öd-Gebieten kann man auch beim Ödfelsland nicht von einer wirklich erwähnenswerten oder lohnenswerten Landwirtschaft reden. Auch die Wasserversorgung lässt sehr zu wünschen übrig. Der einzige Grund, weshalb es immer wieder Menschen in solche Einöden zieht, ist die Verlockung des Reichtums, den man durch den Abbau der zahlreichen Ressourcen erlangen kann.',
        'gebaeude': {'Kartoffelfarm': 25, 'Steinmetz': 100, 'Kiesgrube': 100, 'Auffangbecken': 10, 'Feldbrandziegelei': 100},
    },
    'Steppfelsland': {
        'id': 20, 'startgebiet': True, 'regen_pct': 25,
        'aufwertungen': [], 'abwertungen': [],
        'beschreibung': 'Weite Grassteppen erstrecken sich hier over einen recht steinigen Untergrund. Das Gelände an sich gehört nicht zu den fruchtbarsten, doch es eignet sich recht gut für Tierzuchten. Ansonsten kann das Steppfelsland Ressourcen wie Kies, Lehm, Ton oder Braunkohle anbieten, die man gelegentlich findet. Manchmal auch gewährt das Steppfelsland seinen Bewohnern das, was landläufig als "Schwarzes Gold" bezeichnet wird.',
        'gebaeude': {'Kartoffelfarm': 75, 'Holzfäller': 50, 'Steinmetz': 100, 'kleine Getreidefarm': 50, 'Kiesgrube': 100, 'Auffangbecken': 25, 'Tongrube': 50, 'Lehmgrube': 50, 'Hühnerfarm': 100, 'Feldbrandziegelei': 100},
    },
    'Grünland': {
        'id': 21, 'startgebiet': True, 'regen_pct': 30,
        'aufwertungen': [], 'abwertungen': [],
        'beschreibung': 'Das Grünland ist ein Terrain, das wunderbaren Picknicken auf saftigen, grünen Wiesen einlädt. Wie man an diesen saftigen Wiesen unschwer erkennen kann, bietet der Boden hier gute Startbedingungen für eine reichhaltige Landwirtschaft. Nicht oft, aber immer wieder kommt es vor, dass Kies oder Braunkohle gefunden wird.',
        'gebaeude': {'Orangenplantage': 100, 'Palmenplantage': 75, 'Tabakplantage': 100, 'Kräutergarten': 100, 'Edelholzfäller': 75, 'Auffangbecken': 30, 'Flachsplantage': 100, 'Sägegrube': 50, 'Seidenfarm': 100, 'Seidenspinnerzucht': 100},
    },
    'Savanne': {
        'id': 22, 'startgebiet': True, 'regen_pct': 25,
        'aufwertungen': [], 'abwertungen': [],
        'beschreibung': 'Selten benetzt üppiger Regen den trockenen Savannenboden, doch sind Tiere genügsam. So ziehen große Ziegenherden over die Steppe und ernähren sich von dem gelben, trockenen Gras. Wenige Planzen gedeihen nutzbringend auf dem Boden, doch der, der sich auskennt, kann sich wohl ernähren und kleiden. Oft beherbergt die karge Erde jedoch wertvolle Schätze wie Kies, Lehm oder Ton. Auch kann ab und an Braunkohle und Salpeter gefunden werden.',
        'gebaeude': {'Erdnussfarm': 100, 'Dattelnplantage': 100, 'Palmenplantage': 75, 'Ziegenfarm': 100, 'Edelholzfäller': 50, 'Auffangbecken': 25, 'Tongrube': 80, 'Lehmgrube': 90, 'Flachsplantage': 100, 'Feldbrandziegelei': 100},
    },
    'Grünhügel': {
        'id': 23, 'startgebiet': False, 'regen_pct': 35,
        'aufwertungen': [], 'abwertungen': ['Savannenhügel'],
        'beschreibung': 'Bewohner eines solchen Terrains dürfen eine ähnliche Landschaft wie Bewohner eines Grünlandes erleben. Der sichtbare Unterschied jedoch ist, dass der Grünhügel, wie der Name schon sagt, ein wenig größere Höhenunterschiede hat. Aufgrund der vielen Hügel hat dieses Landschaft allerdings einen kleinen Nachteil in der Produktivität von Plantagen gegenüber dem Grünland. Dafür hat man in Grünhügeln weit bessere Aussichten auf Bodenschätze. Man ein wenig Glück kann man hier Braunkohle, Lehm, Kalkstein, manchmal Salpeter und selten Diamanten finden.',
        'gebaeude': {'Orangenplantage': 75, 'Tabakplantage': 100, 'Kräutergarten': 75, 'Edelholzfäller': 75, 'Auffangbecken': 35, 'Flachsplantage': 100, 'Sägegrube': 50, 'Seidenfarm': 75, 'Seidenspinnerzucht': 100, 'Weingarten': 100},
    },
    'Savannenhügel': {
        'id': 24, 'startgebiet': True, 'regen_pct': 28,
        'aufwertungen': [], 'abwertungen': [],
        'beschreibung': 'Der Savannenhügel ist im Endeffekt lediglich ein etwas besserer Brachhügel. Beide Terrains unterscheiden sich dem Aussehen nach im Groben lediglich um ein wenig Gras. Wirtschaftlich hat dies jedoch weitreichendere Folgen, als es vielleicht auf den ersten Blick ersichtlich ist. Aufgrund der - wenn auch trockenen und mageren - Grasdecke besteht in Savannenhügeln die Möglichkeit auf eine ausgedehnte Zucht von Ziegen. Auch die Wasserversorgung erweist sich hier als besser, als die magere Grasdecke erscheinen lässt. Eines hat der Savannenhügel jedoch mit dem Brachhügel gemeinsam: In diesem Terrain besteht ebenfalls die Chance auf eine Vielzahl verschiedenster Ressourcen, die nur darauf warten, gefunden zu werden.',
        'gebaeude': {'Erdnussfarm': 75, 'Dattelnplantage': 75, 'Ziegenfarm': 100, 'Edelholzfäller': 50, 'Auffangbecken': 28, 'Tongrube': 50, 'Lehmgrube': 75, 'Flachsplantage': 100, 'Feldbrandziegelei': 100},
    },
    'Grüngebirge': {
        'id': 25, 'startgebiet': False, 'regen_pct': 40,
        'aufwertungen': [], 'abwertungen': [],
        'beschreibung': 'Zu dieser Terrainart gehören Landschaftsstriche, die von Gebirgen geprägt sind, jedoch auch Grünflächen aufweisen. Im Gegensatz zu anderen grün bewachsenen Landschaften eignet sich das Grüngebirge jedoch nicht zur Viehzucht. Dafür kann man hier nahezu alle Bodenschätze mit einer akzeptablen Wahrscheinlichkeit finden und die Wasserversorgung ist durch die häufigen Regengüsse im Gebirge ausgezeichnet.',
        'gebaeude': {'Orangenplantage': 25, 'Steinmetz': 100, 'Auffangbecken': 40, 'Sägegrube': 50, 'Weingarten': 50},
    },
    'Savannengebirge': {
        'id': 26, 'startgebiet': False, 'regen_pct': 33,
        'aufwertungen': [], 'abwertungen': [],
        'beschreibung': 'Das Savannengebirge ist ein weiteres der zahlreichen kargeren Terrains. In der Landwirtschaft kann man eine Hand voll Erdnüsse als das höchste der Gefühle bezeichnen, doch für die Versorgung eines größeren Volkes reicht der Ertrag eines Savannengebirges einfach nicht aus. Wasser dagegen wird man hier ausreichend finden können. Betrachtet man jedoch den Bergbau, so wird man feststellen, dass das Savannengebirge ein sehr ertragreiches Terrain ist. Man kann hier jeglich Art von Metallerz finden, aber auch Ton, Bauxit, Kalkstein, Schwefel, Salpeter und Diamanten.',
        'gebaeude': {'Erdnussfarm': 25, 'Steinmetz': 100, 'Auffangbecken': 33, 'Feldbrandziegelei': 100},
    },
    'Grünfelsland': {
        'id': 27, 'startgebiet': True, 'regen_pct': 30,
        'aufwertungen': [], 'abwertungen': [],
        'beschreibung': 'Weite Grüne bewachsene Flächen, die hin und wieder von felsigen Landstrichen unterbrochen werden, machen das Wesen dieser Landschaft aus. Im Grünfelsland sind Nahrung und Wasser, wenn auch nicht üppig, zur Genüge vorhanden. Vor allem bietet sich aber die Möglichkeit Steine zu gewinnen die zum Bau größeren Gebäude als einfachen Holzhütten benötigt werden. Dieses Terrain bietet recht gute Chancen Kies zu finden, gelegentlich findet man Braunkohle und sehr selten kann auch Erdöl gefunden werden.',
        'gebaeude': {'Orangenplantage': 75, 'Steinmetz': 100, 'Tabakplantage': 100, 'Kräutergarten': 75, 'Kiesgrube': 100, 'Edelholzfäller': 75, 'Auffangbecken': 30, 'Sägegrube': 50},
    },
    'Savannenfelsland': {
        'id': 28, 'startgebiet': True, 'regen_pct': 25,
        'aufwertungen': [], 'abwertungen': [],
        'beschreibung': 'Weite Grassteppen erstrecken sich hier over einen recht steinigen Untergrund. Das Gelände an sich gehört nicht zu den fruchtbarsten, doch es eignet sich recht gut zur Zucht von Ziegen. Ansonsten kann das Steppfelsland Ressourcen wie Kies, Lehm, Ton oder Braunkohle anbieten, die man gelegentlich findet. Manchmal auch gewährt das Steppfelsland seinen Bewohnern das, was landläufig als "Schwarzes Gold" bezeichnet wird.',
        'gebaeude': {'Erdnussfarm': 75, 'Dattelnplantage': 75, 'Steinmetz': 100, 'Ziegenfarm': 100, 'Kiesgrube': 100, 'Edelholzfäller': 50, 'Auffangbecken': 25, 'Tongrube': 50, 'Lehmgrube': 50, 'Feldbrandziegelei': 100},
    },
    'Brachland': {
        'id': 29, 'startgebiet': False, 'regen_pct': 6,
        'aufwertungen': ['Savanne', 'Pampa'], 'abwertungen': ['Wüste'],
        'beschreibung': 'So gut wie nie lässt eine Regenwolke hier ihr kostbares Gut fallen. Zwischen den wenigen Pflanzen, die der Umwelt trotzen, leben Bukhts von den Sprossen der hier wachsenden Kakteen. Diese over die Jahrzehnte entstandene Kreuzung aus Trampeltier und Dromedar ist genau so widerstandsfähig und als Last- und Reittier geeignet wie die beiden Rassen aus denen sie entstanden ist. Trotz der Möglichkeit der Versorgung dieser Tiere und dem Anbau einer Hand voll Kakteensprossen, ist das Brachland ist kein angenehmer Ort zum Leben. Große Mengen Lehm können jedoch aus dem Boden gewonnen werden und immer wieder findet sich auch Kies und Sand. Seltener stößt man auf Ton, Braunkohle oder Salpeter. Wenn man tief genug gräbt, hat man sogar die Chance, Erdöl zu finden.',
        'gebaeude': {'Dattelnplantage': 50, 'Auffangbecken': 10, 'Feldbrandziegelei': 100},
    },
    'Brachfelsland': {
        'id': 30, 'startgebiet': False, 'regen_pct': 6,
        'aufwertungen': ['Savannenfelsland', 'Pampafelsland'], 'abwertungen': ['Wüste'],
        'beschreibung': 'Wie bei allen Brach-Gebieten kann man auch beim Brachfelsland nicht von einer wirklich erwähnenswerten oder lohnenswerten Landwirtschaft reden. Auch die Wasserversorgung lässt sehr zu wünschen übrig. Der einzige Grund, weshalb es immer wieder Menschen in solche Einöden zieht, ist die Verlockung des Reichtums, den man durch den Abbau der zahlreichen Ressourcen erlangen kann.',
        'gebaeude': {'Dattelnplantage': 40, 'Steinmetz': 100, 'Kiesgrube': 100, 'Auffangbecken': 10, 'Feldbrandziegelei': 100},
    },
    'Brachhügel': {
        'id': 31, 'startgebiet': False, 'regen_pct': 9,
        'aufwertungen': ['Savannenhügel'], 'abwertungen': ['Sanddünen'],
        'beschreibung': 'Brachhügel sind sehr einsame und einseitige Landschaften, in denen man kaum flache, waagrechte Gebiete findet. Sie bieten zwar Möglichkeit zur Landwirtschaft, doch ist deren Effektivität zu vernachlässigen. Auch die Wasserversorgung kann sich ohne Hilfe von außen manchmal als schwierig erweisen. Solche kargen Landschaften wie Brachhügel eignen sich eher zum Abbau verschiedenster Rohstoffe. Für Ressourcen wie Lehm, Braunkohle und Sand bestehen gute bis sehr gute Chancen auf einen Fund, Kalkstein, Salz, Salpeter und selten auch Diamanten sind jedoch auch zu finden.',
        'gebaeude': {'Dattelnplantage': 40, 'Auffangbecken': 10, 'Feldbrandziegelei': 100},
    },
    'Brachgebirge': {
        'id': 32, 'startgebiet': False, 'regen_pct': 20,
        'aufwertungen': [], 'abwertungen': [],
        'beschreibung': 'Die Attribute brach und gebirgig bezeichnen dieses Terrain am besten. Beinahe keine Nahrungsmittel lassen sich auf dem kargen und steinigen Boden kultivieren, aber es mag einem sehr wohl gelingen, ein paar der berüchtigten Bluescorpions zu fangen, die hier ihr Jagdrevier haben. Durch die Zucht derselben kann man die Nahrungskette im Brachgebirge teilweise herumdrehen. Die eigentliche Stärke dieser Gebiete liegt aber in ihren Vorkommen an Bodenschätzen und Steinen, die sich in Steinbrüchen brechen und abtransportieren lassen.',
        'gebaeude': {'Steinmetz': 100, 'Auffangbecken': 10, 'Feldbrandziegelei': 100},
    },
    'Ozean': {
        'id': 33, 'startgebiet': False, 'regen_pct': 0,
        'aufwertungen': [], 'abwertungen': [],
        'beschreibung': 'Dunkelheit und Tiefseemonster lauern in diesen Gewässern. Dessen ist man sich sicher, immerhin erzählen alte Geschichten von den schaurigen Kreaturen, welche die wagemutigen Halb-Götter alter Tage mithilfe ihrer Stählernen Diener zur Oberfläche brachten. Gut das unsere Fischer selbst keinen Fuss, oder zumindest kaum weiter als ein paar Meter in dieses unerforschte Gebiet vorwagen muss, sondern ihre Netze und Angelleinen diese Arbeit übernehmen lassen. Zudem lassen sich durch Destillation Trinkbares Wasser und Salz herstellen. Nicht umsonst finden sich an der Küste meist einige große Städte, die sowohl durch die Früchte des Meeres, als auch des Handels reich geworden sind.',
        'gebaeude': {},
    },
    'Pampa': {
        'id': 34, 'startgebiet': True, 'regen_pct': 25,
        'aufwertungen': [], 'abwertungen': [],
        'beschreibung': 'Selten benetzt üppiger Regen den trockenen Savannenboden, doch sind Tiere genügsam. So ziehen große Lama- oder Alpakaherden over die Pampa und ernähren sich von den teils öligen Gräsern. Wenige Planzen gedeihen nutzbringend auf dem Boden, doch der, der sich auskennt, kann sich wohl ernähren und kleiden. Oft beherbergt die karge Erde jedoch wertvolle Schätze wie Kies, Lehm oder Ton. Auch kann ab und an Braunkohle und Salpeter gefunden werden. Zudem lässt sich mit genügend Wissen kleine Mengen Industriell nutzbares Öl aus den Gräsern dieses Terrains gewinnen.',
        'gebaeude': {'Dattelnplantage': 100, 'Edelholzfäller': 50, 'Auffangbecken': 25, 'Feldbrandziegelei': 100},
    },
    'Weideland': {
        'id': 35, 'startgebiet': True, 'regen_pct': 30,
        'aufwertungen': [], 'abwertungen': [],
        'beschreibung': 'Das Weideland ist ein Terrain, das wunderbaren Picknicken auf saftigen, grünen Wiesen einlädt. Wie man an diesen saftigen Wiesen unschwer erkennen kann, bietet der Boden hier gute Startbedingungen für eine reichhaltige Landwirtschaft. Nicht oft, aber immer wieder kommt es vor, dass Kies oder Braunkohle gefunden wird.',
        'gebaeude': {'Orangenplantage': 100, 'Tabakplantage': 100, 'Kräutergarten': 100, 'Edelholzfäller': 75, 'Auffangbecken': 30, 'Sägegrube': 50, 'Seidenfarm': 100, 'Seidenspinnerzucht': 100},
    },
    'Regenwald': {
        'id': 36, 'startgebiet': True, 'regen_pct': 50,
        'aufwertungen': [], 'abwertungen': [],
        'beschreibung': 'Wer kennt sie nicht, die Geschichten von Wäldern, die Regelmäßig von kurzen wie heftigen Regengüssen heimgesucht werden, dass man meint gleich Fische in Schulterhöhe vorbeischwimmen zu sehen? Manche dieser Geschichten sind war, andere nicht. Tatsache ist jedoch, dass der Regenwald wie jedes andere Gelände auch Herausforderungen birgt. Wer hier Fuss gefasst hat, wird weder Hunger leiden, noch im freien schlafen müssen. Der Regenwald bietet genügend Nahrungsmittel, Bau- und Edelholz, sowie Produkte wertvoller Plantagen um sich zu versorgen und Handelspartner in aller Welt finden zu können.',
        'gebaeude': {'Orangenplantage': 100, 'Palmenplantage': 100, 'Auffangbecken': 50, 'Nuggretzucht': 100, 'Kautschukplantage': 100, 'Sägegrube': 100, 'Tropenholzfäller': 100, 'Bananenhain': 100},
    },
    'Pampagebirge': {
        'id': 37, 'startgebiet': True, 'regen_pct': 33,
        'aufwertungen': [], 'abwertungen': [],
        'beschreibung': 'Das Pampagebirge ist ein weiteres der zahlreichen kargeren Terrains. In der Landwirtschaft kann man eine Hand voll Datteln als das höchste der Gefühle bezeichnen, doch für die Versorgung eines größeren Volkes reicht der Ertrag eines Pampagebirges einfach nicht aus. Wasser dagegen wird man hier ausreichend finden können. Auch wachsen hier spärliche Flecken der gleichen öligen Gräser wie in der Pampa. Betrachtet man jedoch den Bergbau, so wird man feststellen, dass das Pampagebirge ein sehr ertragreiches Terrain ist. Man kann hier jeglich Art von Metallerz finden, aber auch Ton, Bauxit, Kalkstein, Schwefel, Salpeter und Diamanten.',
        'gebaeude': {'Dattelnplantage': 25, 'Auffangbecken': 33, 'Feldbrandziegelei': 100},
    },
    'Plateau': {
        'id': 38, 'startgebiet': True, 'regen_pct': 40,
        'aufwertungen': [], 'abwertungen': [],
        'beschreibung': 'Ein Plateau – hochgelegenes, weitgehend ebenes Terrain mit guter Wasserversorgung und moderaten landwirtschaftlichen Möglichkeiten.',
        'gebaeude': {'Orangenplantage': 50, 'Auffangbecken': 40, 'Sägegrube': 50},
    },
    'Hochnebelwald': {
        'id': 39, 'startgebiet': True, 'regen_pct': 40,
        'aufwertungen': [], 'abwertungen': [],
        'beschreibung': 'Ein immergrüner Nebelwald in großen Höhen, geprägt durch konstante Feuchtigkeit und üppige Vegetation.',
        'gebaeude': {'Auffangbecken': 40, 'Nuggretzucht': 100, 'Kautschukplantage': 100, 'Teehain': 100, 'Sägegrube': 100, 'Tropenholzfäller': 75, 'Reisfarm': 50, 'Bananenhain': 75},
    },
    'Pampafelsland': {
        'id': 40, 'startgebiet': True, 'regen_pct': 25,
        'aufwertungen': [], 'abwertungen': [],
        'beschreibung': 'Trockene Pampagrassteppen over steinigem Untergrund. Gut für Tierzucht und Rohstoffabbau.',
        'gebaeude': {'Dattelnplantage': 75, 'Steinmetz': 100, 'Kiesgrube': 100, 'Edelholzfäller': 50, 'Auffangbecken': 25, 'Feldbrandziegelei': 100},
    },
    'Weidefelsland': {
        'id': 41, 'startgebiet': True, 'regen_pct': 30,
        'aufwertungen': [], 'abwertungen': [],
        'beschreibung': 'Grüne Weiden over felsigem Boden – gute Bedingungen für Landwirtschaft und Steingewinnung.',
        'gebaeude': {'Orangenplantage': 75, 'Steinmetz': 100, 'Kiesgrube': 100, 'Edelholzfäller': 75, 'Auffangbecken': 30, 'Sägegrube': 50},
    },
    'Steinwüste': {
        'id': 42, 'startgebiet': False, 'regen_pct': 6,
        'aufwertungen': [], 'abwertungen': [],
        'beschreibung': 'Eine steinige, extrem trockene Wüste. Steinabbau ist möglich, Landwirtschaft nahezu unmöglich.',
        'gebaeude': {'Steinmetz': 100, 'Kiesgrube': 100, 'Auffangbecken': 10},
    },
}

def seed():
    conn = get_connection()
    c = conn.cursor()
    ins = upd = 0
    print("\n🔹 Terrain-Typen:")
    for name, td in TERRAIN_DATA.items():
        data = {
            "id": td["id"],
            "name": name,
            "startgebiet": td["startgebiet"],
            "regen_pct": td["regen_pct"],
            "aufwertungen": td["aufwertungen"],
            "abwertungen": td["abwertungen"],
            "beschreibung": td["beschreibung"],
            "gebaeude_effektivitaet": td["gebaeude"]
        }
        if save_entity(c, "terrain_typen", data):
            print(f"  ✅  ID {td['id']:>2} | {name} – neu")
            ins += 1
        else:
            upd += 1
    conn.commit()
    conn.close()
    print(f"   → {ins} neu, {upd} aktualisiert")
    return ins, upd

if __name__ == "__main__":
    seed()
