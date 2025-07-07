// --- TELEGRAM MINI APPS ANALYTICS SDK ENTEGRASYONU ---

// Telegram WebApp context kontrolü
let tg = window.Telegram && window.Telegram.WebApp;
let currentUser = null;

// WebApp hazır olduğunda kullanıcı bilgilerini al
if (tg && tg.initDataUnsafe && tg.initDataUnsafe.user) {
    tg.ready();
    tg.expand();
    currentUser = tg.initDataUnsafe.user;
    console.log("Telegram WebApp context bulundu:", currentUser);
} else {
    console.log("Telegram WebApp context bulunamadı, URL parametrelerinden kullanıcı ID'si aranıyor...");
    
    // URL'den kullanıcı ID'sini almaya çalış
    const urlParams = new URLSearchParams(window.location.search);
    console.log("URL parametreleri:", window.location.search);
    console.log("URL parametreleri objesi:", Object.fromEntries(urlParams));
    const userId = urlParams.get('user_id') || urlParams.get('tgWebAppData');
    console.log("Bulunan user_id:", userId);
    
    if (userId) {
        console.log("URL'den kullanıcı ID'si alındı:", userId);
        currentUser = {
            id: parseInt(userId),
            first_name: "User",
            username: "user"
        };
    } else {
        // Sadece local development için test modu
        const isLocalhost = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
        
        if (isLocalhost) {
            console.log("Local development: Test modu kullanılıyor");
            currentUser = {
                id: 863116061, // Test kullanıcı ID'si
                first_name: "saseyuu",
                username: "saseyuu"
            };
        } else {
            console.error("Production: Telegram WebApp context bulunamadı!");
            // Hata mesajı göster
            showErrorMessage("Telegram WebApp context bulunamadı. Lütfen Telegram'dan açın.");
        }
    }
}

console.log("WebApp kullanıcı ID'si:", currentUser.id);

// Log seviyesi kontrolü
const isProduction = window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1';
const LOG_LEVEL = isProduction ? 'ERROR' : 'DEBUG'; // Production'da sadece hatalar

function log(level, message, data = null) {
    if (level === 'ERROR' || LOG_LEVEL === 'DEBUG') {
        if (data) {
            console.log(`[${level}] ${message}`, data);
        } else {
            console.log(`[${level}] ${message}`);
        }
    }
}

// WebApp yüklendiğinde otomatik olarak kullanıcı verilerini yükle
setTimeout(async () => {
    log('INFO', "WebApp yüklendi, kullanıcı verileri yükleniyor...");
    await fetchUserStats();
    log('INFO', "WebApp yükleme tamamlandı, userStats:", userStats);
}, 1000);


// --- Oyun Konfigürasyonu ---
let db = null;

// Firebase'i başlat
async function initFirebase() {
  try {
    console.log("Firebase config alınıyor...");
    
    // Firebase config'ini backend'den al
    const response = await fetch('https://peacebot-641906716058.europe-central2.run.app/get_firebase_config');
    const firebaseConfig = await response.json();
    
    console.log("Firebase başlatılıyor...");
    firebase.initializeApp(firebaseConfig);
    db = firebase.firestore();
    console.log("Firebase başarıyla başlatıldı");
  } catch (error) {
    console.error("Firebase başlatma hatası:", error);
  }
}

// Firebase'i başlat
initFirebase();

let userStats = { username: "Player", score: 0, total_score: 0, total_pmno_coins: 0 };

console.log("Kullanıcı verileri ayarlandı:", userStats);

// -- Firebase Config (web için sadece okuma yapılacak!)
// Firebase'i skor tablosu için sadece KULLANICIYA SKOR GÖSTERMEK için yüklemek istiyorsan, kendi config ile ekle! Yazma işini bot.py yapacak, webden yazma YOK! (Yorum satırı bıraktım!)
async function fetchUserStats() {
  log('DEBUG', "=== fetchUserStats başladı ===");
  
  if (!currentUser) {
    log('ERROR', "fetchUserStats: currentUser bulunamadı");
    return;
  }
  
  log('DEBUG', "fetchUserStats: currentUser.id =", currentUser.id);
  log('DEBUG', "fetchUserStats: currentUser =", currentUser);
  
  try {
    const ref = db.collection("users").doc(String(currentUser.id));
    log('DEBUG', "fetchUserStats: Firebase path =", `users/${currentUser.id}`);
    
    const snap = await ref.get();
    log('DEBUG', "fetchUserStats: Firebase response exists =", snap.exists);
    
    if (snap.exists) {
      userStats = snap.data();
      log('INFO', "fetchUserStats: Kullanıcı verisi yüklendi =", userStats);
    } else {
      log('INFO', "fetchUserStats: Kullanıcı verisi bulunamadı");
    }
  } catch (error) {
    log('ERROR', "fetchUserStats: Firebase hatası =", error);
  }
  
  log('DEBUG', "=== fetchUserStats bitti ===");
}


// --- Leaderboard Getir ---
async function fetchLeaderboard() {
  const snap = await db.collection("users").orderBy("total_score", "desc").limit(5).get();
  return snap.docs.map(doc => doc.data());
}

const MEME_MESSAGES = [
  { 
    text: "Dove: 'One more step for peace!'", 
    img: "dove_peace" 
  },
  { 
    text: "Peace Bro: 'Kid, you rock!'", 
    img: "peace_bro" 
  },
  { 
    text: "Missile turned into a dove. Classic!", 
    img: "missile_to_dove"
  },
  { 
    text: "Tweet tweet! Bombs out, peace in!", 
    img: "twitter_bird" 
  },
  { 
    text: "Everyone for peace!", 
    img: "crowd_peace" 
  }
];


// --- Oyun Ayarları ---
const buildingData = {
    iran: [
        { x: 100, y: 400 },
        { x: 170, y: 410 },
        { x: 260, y: 410 },
        { x: 60, y: 470 },
        { x: 140, y: 520 },
        { x: 260, y: 520 },
        { x: 320, y: 470 },
        { x: 320, y: 560 },
        { x: 100, y: 580 },
        { x: 250, y: 620 }
    ],
    israel: [
        { x: 120, y: 480 },
        { x: 210, y: 430 },
        { x: 270, y: 480 },
        { x: 80, y: 550 },
        { x: 170, y: 530 },
        { x: 250, y: 550 },
        { x: 320, y: 540 },
        { x: 360, y: 600 },
        { x: 120, y: 640 },
        { x: 230, y: 670 }
    ]
};
// Binalar için örnek health
const BUILDING_HEALTH = 2;

// --- Asset paths ---
const assets = {
    iran_bg: 'assets/iran_bg.jpg',
    israel_bg: 'assets/israel_bg.jpg',
    lobby_bg: 'assets/lobby_bg.png',
    logo: 'assets/logo.png',
    destroyed_building: 'assets/destroyed_building.png',
    rocket: 'assets/rocket.png',
    explosion: 'assets/explosion.gif',
    dove: 'assets/dove.png',
    coin: 'assets/coin_icon.png',
    score_icon: 'assets/score_icon.png',
    button:'assets/play_button.png',
    building_bar:'assets/score.png',
    smoke: 'assets/smoke_sheet.png',
    dove_peace: 'assets/dove_peace.png',
    peace_bro: 'assets/peace_bro.png',
    missile_to_dove: 'assets/missile_to_dove.png',
    twitter_bird: 'assets/twitter_bird.png',
    crowd_peace: 'assets/crowd_peace.png',
};

// --- Global state ---
let globalUserData = {
    username: "Player",
    maxScore: 0,
    totalScore: 0,
    coins: 0,
    leaderboard: []
};

/**
 * Phaser 3'te farklı ekran boyutlarına uyumlu (responsive) bir lobi sahnesi.
 * Bu yaklaşım, elemanları ekranın köşelerine, kenarlarına veya merkezine sabitleyerek
 * ve birbirlerine göre konumlandırarak çalışır. Bu sayede farklı en-boy oranlarında
 * tutarlı bir görünüm elde edilir.
 */
/**
 * Phaser 3 için Lobi Sahnesi.
 * Farklı ekran boyutlarına uyumlu olacak şekilde düzenlenmiştir.
 */
class LobbyScene extends Phaser.Scene {
    constructor() {
        super('LobbyScene');
    }

    async create() {
        // --- 1. Temel Değişkenler ---
        const { width, height } = this.scale;
        const margin = width * 0.05;

        // --- 2. Arka Plan ---
        // Arka planı genişliğe sığacak şekilde ölçeklendirip üste hizalıyoruz.
        // Bu sayede "PEACE" ve kuş logosu her zaman görünür kalır.
        const bg = this.add.image(width / 2, 0, 'lobby_bg').setOrigin(0.5, 0);
        const bgScale = width / bg.width;
        bg.setScale(bgScale);

        // --- 3. Kullanıcı İstatistikleri Paneli (Sağ Üst) ---
        console.log("LobbyScene: fetchUserStats çağrılıyor...");
        try {
            await fetchUserStats();
            console.log("LobbyScene: fetchUserStats tamamlandı");
            console.log("LobbyScene: userStats =", userStats);
        } catch (error) {
            console.error("Kullanıcı istatistikleri alınamadı:", error);
            window.userStats = { username: 'Player', score: 0, total_score: 0, total_pmno_coins: 0 };
        }
        
        const statsX = width - margin;
        let statsY = height * 0.05;
        const statColor = "#ffe349";
        const smallFontSize = Math.min(width * 0.03, 20);
        const welcomeFontSize = smallFontSize + 2;

        this.add.text(statsX, statsY, `Welcome, ${userStats.username || 'Player'}!`, { font: `${welcomeFontSize}px monospace`, fill: "#fff", align: 'right' }).setOrigin(1, 0);
        statsY += welcomeFontSize + 12;
        this.add.text(statsX, statsY, `Max Score: ${userStats.score}`, { font: `${smallFontSize}px monospace`, fill: statColor, align: 'right' }).setOrigin(1, 0);
        statsY += smallFontSize + 9;
        this.add.text(statsX, statsY, `Total Score: ${userStats.total_score}`, { font: `${smallFontSize}px monospace`, fill: statColor, align: 'right' }).setOrigin(1, 0);
        statsY += smallFontSize + 9;
        this.add.text(statsX, statsY, `MNW Coins: ${userStats.total_pmno_coins}`, { font: `${smallFontSize}px monospace`, fill: statColor, align: 'right' }).setOrigin(1, 0);

        // Cüzdan adresi gösterimi ve bağlama butonu
        let walletY = statsY + smallFontSize + 16;
        const walletFontSize = smallFontSize;
        let walletText = this.add.text(statsX, walletY, '', { font: `${walletFontSize}px monospace`, fill: '#43f3c7', align: 'right' }).setOrigin(1, 0);

        // Eğer userStats.wallet_address varsa göster
        if (userStats.wallet_address) {
            walletText.setText(`Wallet: ${userStats.wallet_address.slice(0, 8)}...`);
        } else {
            walletText.setText('Wallet: Not connected');
        }

        const walletBtn = this.add.text(statsX, walletY + walletFontSize + 8, '🔗 Cüzdanını Bağla', {
            font: `${walletFontSize}px monospace`,
            fill: '#fff',
            backgroundColor: '#1a1a1a',
            padding: { left: 10, right: 10, top: 4, bottom: 4 },
            align: 'right'
        }).setOrigin(1, 0).setInteractive({ cursor: 'pointer' });

        walletBtn.on('pointerup', async () => {
            // Kullanıcıdan cüzdan adresi iste
            const address = prompt('Telegram Wallet adresinizi girin:');
            if (!address) return;
            // Backend'e kaydet
            try {
                const response = await fetch('https://peacebot-641906716058.europe-central2.run.app/save_wallet', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ user_id: currentUser.id, wallet_address: address })
                });
                const result = await response.json();
                if (result.success) {
                    walletText.setText(`Wallet: ${address.slice(0, 8)}...`);
                    alert('Cüzdan adresiniz kaydedildi!');
                } else {
                    alert('Cüzdan adresi kaydedilemedi: ' + (result.error || 'Bilinmeyen hata'));
                }
            } catch (e) {
                alert('Cüzdan adresi kaydedilemedi: ' + e.message);
            }
        });

        // --- 4. Merkezi Elemanlar ---

        // "Start Mission" Butonu
        const startBtn = this.add.image(width / 2, height * 0.58, 'button')
            .setInteractive({ cursor: 'pointer' });
        startBtn.setScale(width * 0.0015); // Buton boyutunu ayarla
        startBtn.on('pointerup', () => this.scene.start('SideSelectScene'));
        // Not: Buton üzerindeki "START MISSION" yazısı kaldırıldı, çünkü resimde mevcut.

        // Logo (Butonun ÜSTÜNE konumlandırılır)
        const logoY = startBtn.y - startBtn.displayHeight / 2 - (height * 0.06);
        const logo = this.add.image(width / 2, logoY, 'logo');
        logo.setScale(width * 0.001); // Logo boyutunu ayarla

        // Alt Menü Linkleri (Butonun ALTINA konumlandırılır)
        const menuY = startBtn.y + startBtn.displayHeight / 2 + (height * 0.04);
        const menuFontSize = Math.min(width * 0.035, 24);

        this.add.text(width * 0.25, menuY, "Leaderboard", { font: `${menuFontSize}px monospace`, fill: "#ffe349" })
          .setOrigin(0.5, 0).setInteractive({ cursor: 'pointer' })
          .on('pointerup', () => this.scene.start('LeaderboardScene'));

        this.add.text(width * 0.75, menuY, "How to Play?", { font: `${menuFontSize}px monospace`, fill: "#43c0f7" })
          .setOrigin(0.5, 0).setInteractive({ cursor: 'pointer' })
          .on('pointerup', () => this.scene.start('HowToPlayScene'));

        // --- 5. Liderlik Tablosu (Ekranın ALTINA sabitlenmiş) ---
        const leaderboardY = height - (height * 0.18); // Ekranın alt kısmında konumlandır
        const midFontSize = Math.min(width * 0.04, 28);

        this.add.text(width / 2, leaderboardY, "Top Players", {
            font: `bold ${midFontSize}px monospace`,
            fill: "#ffe349"
        }).setOrigin(0.5, 0);

        try {
            const leaders = (await fetchLeaderboard()).slice(0, 3);
            let leaderYPos = leaderboardY + midFontSize + 10;
            leaders.forEach((u, i) => {
                this.add.text(width / 2, leaderYPos + i * (smallFontSize + 8),
                    `${i + 1}. ${u.username || 'Anon'} - ${u.total_score} pts`, {
                        font: `${smallFontSize}px monospace`,
                        fill: "#fff"
                    }).setOrigin(0.5, 0);
            });
        } catch (error) {
            console.error("Liderlik tablosu alınamadı:", error);
        }
    }
}


// --- Responsive Boyutlar ve Helper ---
function getScaleVars(scene) {
  // Boyutları ekrana oranla al, minimum ve maksimum koy
  const w = scene.cameras.main.width;
  const h = scene.cameras.main.height;
  return {
    w, h,
    fontBig: Math.max(Math.round(w/20), 18),
    fontMid: Math.max(Math.round(w/25), 15),
    fontSmall: Math.max(Math.round(w/32), 12),
    btnScale: Math.max(w/1400, 0.33),
    logoScale: Math.max(w/700, 0.21),
    topPanelW: Math.min(w * 0.55, 330),
    margin: Math.max(w/48, 10)
  };
}

// --- Taraf Seçim ---
class SideSelectScene extends Phaser.Scene {
    constructor() { super({ key: 'SideSelectScene' }); }
    create() {
        this.cameras.main.setBackgroundColor("#000");
        this.add.text(this.cameras.main.centerX, 120, "Choose your side", { font: '32px monospace', color: "#fff" }).setOrigin(0.5);

        // İran
        let iranImg = this.add.image(this.cameras.main.centerX - 100, 250, 'iran_bg').setDisplaySize(120, 160).setInteractive();
        this.add.text(this.cameras.main.centerX - 100, 335, "Defend Iran", { font: '20px monospace', color: "#fff" }).setOrigin(0.5, 0);

        // İsrail
        let isrImg = this.add.image(this.cameras.main.centerX + 100, 250, 'israel_bg').setDisplaySize(120, 160).setInteractive();
        this.add.text(this.cameras.main.centerX + 100, 335, "Defend Israel", { font: '20px monospace', color: "#fff" }).setOrigin(0.5, 0);

        iranImg.on('pointerdown', () => { this.scene.start('GameScene', { side: 'iran' }); });
        isrImg.on('pointerdown', () => { this.scene.start('GameScene', { side: 'israel' }); });
    }
}

class BootScene extends Phaser.Scene {
    constructor() { super('BootScene'); }
    preload() {
        this.load.image('iran_bg', assets.iran_bg);
        this.load.image('israel_bg', assets.israel_bg);
        this.load.image('lobby_bg', assets.lobby_bg);
        this.load.image('logo', assets.logo);
        this.load.image('destroyed_building', assets.destroyed_building);
        this.load.image('rocket', assets.rocket);
        this.load.image('dove', assets.dove);
        this.load.image('coin_icon', assets.coin);
        this.load.image('score_icon', assets.score_icon);
        this.load.image('button', assets.button);
        this.load.image('building_bar', assets.building_bar);
        this.load.image('dove_peace', assets.dove_peace);
        this.load.image('peace_bro', assets.peace_bro);
        this.load.image('missile_to_dove', assets.missile_to_dove);
        this.load.image('twitter_bird', assets.twitter_bird);
        this.load.image('crowd_peace', assets.crowd_peace);

        this.load.spritesheet('explosion', assets.explosion, { frameWidth: 64, frameHeight: 64 });
        this.load.spritesheet('smoke', assets.smoke, { frameWidth: 128, frameHeight: 128});
    }
    create() {
        this.scene.start('LobbyScene');
    }
}


// --- Oyun ---
const POWERUP_TYPES = ["extra_dove", "double_score", "slow_rockets", "freeze"];

class GameScene extends Phaser.Scene {
    constructor() { super({ key: 'GameScene' }); }

    create(data) {
        // --- Temel ayarlar ---
        let side = data && data.side ? data.side : "israel";
        this.add.text(50, 50, `SIDE: ${side}`, { font: '24px monospace', color: "#fff" });
        this.add.image(
            this.cameras.main.centerX,
            this.cameras.main.centerY,
            side === "iran" ? "iran_bg" : "israel_bg"
        ).setDisplaySize(this.cameras.main.width, this.cameras.main.height);
        // Binalar
        this.buildings = [];
        let bArr = buildingData[side];
        for (let b of bArr) {
            let building = this.add.rectangle(b.x, b.y, 50, 60, 0xffffff, 0.01);
            building.health = BUILDING_HEALTH;
            building.side = side;
            building.alive = true;
            building.setInteractive();
            this.buildings.push(building);
            building.healthBar = this.add.graphics();
            this.updateHealthBar(building);
        }

        // Skor & puan
        this.score = 0;
        this.scoreText = this.add.text(30, 20, "Score: 0", { font: '24px monospace', color: "#fff" });

        // Dinamik zorluk
        this.rocketCount = 0;
        this.bombSpawnDelay = 1100;
        this.bombSpeedMultiplier = 1;
        this.doubleScoreActive = false;
        this.nextMemeAt = Phaser.Math.Between(8, 12); // İlk meme için başlangıç
        // Zorluk seviyeleri
        this.difficultyLevels = [
            { count: 0,   delay: 1100, speed: 1.00 },
            { count: 20,  delay: 950,  speed: 1.15 },
            { count: 50,  delay: 800,  speed: 1.30 },
            { count: 100, delay: 650,  speed: 1.50 },
            { count: 150, delay: 500,  speed: 1.80 },
            { count: 200, delay: 390,  speed: 2.10 }
        ];

        // Dinamik puan tablosu
        this.scoreTable = [
            { max: 20,  min: 7, maxP: 10 },
            { max: 70,  min: 5, maxP: 8 },
            { max: 999, min: 3, maxP: 6 }
        ];

        // Günlük görev (localStorage)
        this.today = new Date().toISOString().slice(0, 10);
        this.localMissions = JSON.parse(localStorage.getItem("missions") || "{}");
        if (!this.localMissions[this.today]) {
            this.localMissions[this.today] = { rockets: 0, claimed: false };
        }
        this.hourlyPlayCount = parseInt(localStorage.getItem("hourlyPlayCount") || "0");
        this.lastPlayHour = parseInt(localStorage.getItem("lastPlayHour") || "0");


        // Saatlik limit kontrolü
        let nowHour = new Date().getHours();
        if (this.lastPlayHour !== nowHour) {
            this.hourlyPlayCount = 0;
            localStorage.setItem("hourlyPlayCount", "0");
            localStorage.setItem("lastPlayHour", nowHour.toString());
        }

        // Power-up timer
        this.time.addEvent({
            delay: Phaser.Math.Between(30000, 60000),
            callback: () => this.spawnPowerUp(),
            callbackScope: this,
            loop: true
        });

        // Oyun timer
        this.startBombTimer();

        // Oyun bitti mi?
        this.gameOver = false;
    }

    // --- Power-up spawn ---
    spawnPowerUp() {
        let type = Phaser.Utils.Array.GetRandom(POWERUP_TYPES);
        let x = Phaser.Math.Between(60, this.cameras.main.width - 60);
        let y = Phaser.Math.Between(70, this.cameras.main.height - 150);
        let spriteKey = type === "extra_dove" ? 'dove' : 'coin_icon';
        let pu = this.physics.add.sprite(x, y, spriteKey).setScale(0.6).setInteractive();

        pu.on('pointerdown', () => {
            this.activatePowerUp(type);
            pu.destroy();
        });
        this.time.delayedCall(8000, () => pu.destroy());
    }

    // --- Power-up etkileri ---
    activatePowerUp(type) {
        if (type === "double_score") {
            this.doubleScoreActive = true;
            this.time.delayedCall(10000, () => this.doubleScoreActive = false);
        }
        if (type === "slow_rockets") {
            this.bombSpeedMultiplier *= 0.6;
            this.time.delayedCall(7000, () => this.adjustDifficulty());
        }
        if (type === "freeze") {
            this.bombTimer.paused = true;
            this.time.delayedCall(4000, () => this.bombTimer.paused = false);
        }
        if (type === "extra_dove") {
            for(let i=0; i<3; i++) this.spawnBomb();
        }
    }

    // --- Günlük görev kontrol ---
    onRocketConverted() {
        // Görev artır
        this.localMissions[this.today].rockets += 1;
        localStorage.setItem("missions", JSON.stringify(this.localMissions));
        // Ödül animasyonu
        if (!this.localMissions[this.today].claimed && this.localMissions[this.today].rockets >= 100) {
            this.localMissions[this.today].claimed = true;
            localStorage.setItem("missions", JSON.stringify(this.localMissions));
            this.showDailyMissionReward();
        }
    }

    showDailyMissionReward() {
        // Basit animasyon veya popup
        let r = this.add.text(this.cameras.main.centerX, this.cameras.main.centerY, "Günlük Görev Başarıldı!\n+50 Coin!", {
            font: "28px monospace",
            fill: "#ff0",
            align: "center",
            backgroundColor: "#222",
            padding: 16
        }).setOrigin(0.5);
        this.time.delayedCall(2200, () => r.destroy());
        // Coin ödülü için ekleme kodu senin coin logicine bağlı
    }

    // --- Bomb timer başlat ---
    startBombTimer() {
        this.bombTimer = this.time.addEvent({
            delay: this.bombSpawnDelay,
            callback: () => {
                if (this.gameOver) return;
                // Saatlik limit ve captcha kontrolü
                this.hourlyPlayCount += 1;
                localStorage.setItem("hourlyPlayCount", this.hourlyPlayCount.toString());
              
                this.rocketCount++;
                this.adjustDifficulty();
                this.spawnBomb();
                // Timer delay’ini güncelle!
                this.bombTimer.reset({
                    delay: this.bombSpawnDelay,
                    callback: this.bombTimer.callback,
                    callbackScope: this
                });
            },
            callbackScope: this,
            loop: true
        });
    }

 

    // --- Zorluk seviyesini güncelle ---
    adjustDifficulty() {
        for (let i = this.difficultyLevels.length - 1; i >= 0; i--) {
            if (this.rocketCount >= this.difficultyLevels[i].count) {
                this.bombSpawnDelay = this.difficultyLevels[i].delay;
                this.bombSpeedMultiplier = this.difficultyLevels[i].speed;
                break;
            }
        }
    }

    // --- Dinamik puan hesapla ---
    getDynamicScore(rocketIndex) {
        for (let i = 0; i < this.scoreTable.length; i++) {
            if (rocketIndex <= this.scoreTable[i].max) {
                return Phaser.Math.Between(this.scoreTable[i].min, this.scoreTable[i].maxP);
            }
        }
        return 3;
    }

    // --- Bombaları spawnla (güncellenmiş spawn algoritması) ---
    spawnBomb() {
        if (this.gameOver) return;

        let liveBuildings = this.buildings.filter(b => b.alive);
        if (liveBuildings.length === 0) return;
        let target = Phaser.Utils.Array.GetRandom(liveBuildings);

        let fromSide = Math.random() < 0.25;
        let x, y, vx, vy;

        if (!fromSide) {
            x = target.x;
            y = -60;
            vx = 0;
            vy = Phaser.Math.Between(170, 240) * this.bombSpeedMultiplier;
        } else {
            let sideLeft = Math.random() < 0.5;
            let offsetY = Phaser.Math.Between(100, 180);
            if (sideLeft) {
                x = -40;
                y = Math.max(target.y - offsetY, 30);
                vx = Phaser.Math.Between(150, 230) * this.bombSpeedMultiplier;
                vy = Phaser.Math.Between(100, 200) * this.bombSpeedMultiplier;
            } else {
                x = this.cameras.main.width + 40;
                y = Math.max(target.y - offsetY, 30);
                vx = -Phaser.Math.Between(150, 230) * this.bombSpeedMultiplier;
                vy = Phaser.Math.Between(100, 200) * this.bombSpeedMultiplier;
            }
        }

        let bomb = this.physics.add.sprite(x, y, 'rocket');
        bomb.setDisplaySize(32, 50);
        bomb.target = target;
        bomb.setInteractive();
        bomb.vx = vx / 1000;
        bomb.vy = vy / 1000;
        this.bombs = this.bombs || [];
        this.bombs.push(bomb);
        bomb.rotation = Math.atan2(bomb.vy, bomb.vx) + Math.PI / 2;

        bomb.on('pointerdown', () => {
            this.bombExplode(bomb, false);
        });
    }

    // --- Oyun döngüsü ---
    update(time, delta) {
        if (this.gameOver) return;
        if (this.bombs) {
            for (let bomb of this.bombs) {
                if (!bomb.active) continue;
                bomb.x += bomb.vx * delta;
                bomb.y += bomb.vy * delta;
                let b = bomb.target;
                if (b && b.alive && Phaser.Geom.Rectangle.Contains(b.getBounds(), bomb.x, bomb.y)) {
                    this.bombExplode(bomb, true);
                }
                if (bomb.y > this.cameras.main.height + 60 || bomb.x < -40 || bomb.x > this.cameras.main.width + 40) {
                    bomb.destroy();
                }
            }
            this.bombs = this.bombs.filter(b => b.active);
        }
        for (let b of this.buildings) {
            this.updateHealthBar(b);
        }
    }

    // --- Bombanın patlama mantığı (puan, görev, power-up, meme!) ---
    bombExplode(bomb, isHitBuilding) {
        if (!bomb.active) return;
        let exp = this.add.sprite(bomb.x, bomb.y, 'explosion').setScale(0.8);
        this.time.delayedCall(400, () => exp.destroy());

        if (!isHitBuilding) {
            let dove = this.add.image(bomb.x, bomb.y, 'dove').setScale(0.35);
            this.tweens.add({
                targets: dove, y: dove.y - 80, alpha: 0,
                duration: 700, onComplete: () => dove.destroy()
            });

            let dynamicScore = this.getDynamicScore(this.rocketCount);
            if (this.doubleScoreActive) dynamicScore *= 2;
            this.score += dynamicScore;
            this.scoreText.setText(`Score: ${this.score}`);

            this.onRocketConverted();

            if (this.rocketCount >= this.nextMemeAt) {
                this.showRandomMeme();
                // bir dahaki sefer için yeni aralık:
                this.nextMemeAt = this.rocketCount + Phaser.Math.Between(8, 12);
            }
            
        }

        if (isHitBuilding && bomb.target) {
            let b = bomb.target;
            if (b.alive) {
                b.health -= 1;
                if (b.health <= 0) {
                    b.alive = false;
                    let des = this.add.image(b.x, b.y + 15, 'destroyed_building').setDisplaySize(90, 100);
                    let smoke = this.add.sprite(b.x, b.y - 10, 'smoke').setScale(0.7);
                    this.time.delayedCall(900, () => smoke.destroy());
                    showSmoke(this, b.x, b.y - 20);
                }
                if (this.buildings.filter(bb => bb.alive).length === 0) {
                    this.gameOver = true;
                    let coinEarned = Math.floor(this.score / 10);
                    this.scene.start('GameOverScene', { score: this.score, coins: coinEarned });
                }
            }
        }
        bomb.destroy();
    }

    // --- Sağlık barı ---
    updateHealthBar(building) {
        if (!building.healthBar) return;
        building.healthBar.clear();
        if (!building.alive) return;
        let w = 38, h = 7;
        building.healthBar.fillStyle(0x008800, 0.7);
        building.healthBar.fillRect(building.x - w / 2, building.y - 36, w * (building.health / BUILDING_HEALTH), h);
        building.healthBar.lineStyle(1, 0xffffff, 1);
        building.healthBar.strokeRect(building.x - w / 2, building.y - 36, w, h);
    }

    // --- Random meme veya Barış Abi mesajı (örnek) ---
showRandomMeme() {
  const meme = Phaser.Utils.Array.GetRandom(MEME_MESSAGES);
  const cx = this.cameras.main.centerX;
  // Görseli biraz daha büyük koyduk
  const img = this.add.image(cx, 60, meme.img)
    .setScale(0.7)        // eskiden 0.25 idi
    .setOrigin(0.5, 0);

  const txt = this.add.text(
    cx,
    img.y + img.displayHeight + 8,
    meme.text,
    {
      font: "18px monospace",
      fill: "#fff",
      backgroundColor: "#1a1a1ac9",
      align: "center",
      padding: { left: 8, right: 8, top: 2, bottom: 2 },
      wordWrap: { width: 260 }
    }
  ).setOrigin(0.5, 0);

  // 1.7 saniye sonra kesin silinsin
  this.time.delayedCall(2300, () => {
    img.destroy();
    txt.destroy();
  });
}


}

// --- GameOver Scene ---
class GameOverScene extends Phaser.Scene {
    constructor() { super({ key: 'GameOverScene' }); }
    async create(data) {
        console.log("=== GameOverScene başladı ===");
        console.log("GameOverScene data:", data);
        console.log("GameOverScene currentUser:", currentUser);
        console.log("GameOverScene db:", db);
        
        this.cameras.main.setBackgroundColor("#222");
        this.add.text(this.cameras.main.centerX, 200, "Game Over!", { font: '36px monospace', color: "#fff" }).setOrigin(0.5);
        this.add.text(this.cameras.main.centerX, 250, `Score: ${data.score}`, { font: '28px monospace', color: "#ffd" }).setOrigin(0.5);
        this.add.text(this.cameras.main.centerX, 290, `MNW Coin: ${data.coins}`, { font: '24px monospace', color: "#3f6" }).setOrigin(0.5);

        // Skoru bot'a kaydet
        console.log("sendScoreToBot çağrılıyor...");
        try {
            await sendScoreToBot(data.score);
            console.log("sendScoreToBot tamamlandı");
        } catch (error) {
            console.log("Bot'a skor gönderilemedi, oyun devam ediyor:", error);
        }
        console.log("=== GameOverScene bitti ===");

        // --- Butonlar (Alt Alta Düzenlenmiş) ---
        const btnY = 360;
        const btnSpacing = 70; // Butonlar arası dikey mesafe
        const btns = [];
        
        // Play Again
        const playAgainBtn = this.add.text(this.cameras.main.centerX, btnY, "🔄 Play Again", { font: '24px monospace', color: "#1df", backgroundColor: "#133" })
            .setOrigin(0.5).setPadding(10).setInteractive();
        playAgainBtn.on('pointerdown', () => { this.scene.start('LobbyScene'); });
        btns.push(playAgainBtn);
        
        // Main Menu
        const mainMenuBtn = this.add.text(this.cameras.main.centerX, btnY + btnSpacing, "🏠 Main Menu", { font: '24px monospace', color: "#fff", backgroundColor: "#222" })
            .setOrigin(0.5).setPadding(10).setInteractive();
        mainMenuBtn.on('pointerdown', () => { this.scene.start('LobbyScene'); });
        btns.push(mainMenuBtn);
        
        // Leaderboard
        const leaderboardBtn = this.add.text(this.cameras.main.centerX, btnY + btnSpacing * 2, "📊 Leaderboard", { font: '24px monospace', color: "#ffe349", backgroundColor: "#222" })
            .setOrigin(0.5).setPadding(10).setInteractive();
        leaderboardBtn.on('pointerdown', () => { this.scene.start('LeaderboardScene'); });
        btns.push(leaderboardBtn);
        
        // Help
        const helpBtn = this.add.text(this.cameras.main.centerX, btnY + btnSpacing * 3, "❓ Help", { font: '22px monospace', color: "#67f", backgroundColor: "#222" })
            .setOrigin(0.5).setPadding(8).setInteractive();
        helpBtn.on('pointerdown', () => { this.scene.start('HowToPlayScene'); });
        btns.push(helpBtn);
    }
}


// --- How to Play ve Leaderboard ekranı ekle ---
class HowToPlayScene extends Phaser.Scene {
  constructor() { super('HowToPlayScene'); }
  create() {
    const vars = getScaleVars(this);
    this.add.rectangle(vars.w/2, vars.h/2, vars.w, vars.h, 0x000000, 0.96);
    this.add.text(vars.w/2, vars.h*0.1, "Rules", { font: `${vars.fontBig}px monospace`, fill: "#fff" }).setOrigin(0.5);
   let msg = "🕊️ Welcome to Peace Missile! 🕊️\n\n" +
    "Turn missiles into doves\n\n" + "and bring peace to the world.\n\n" +
    "Each conversion earns you points.\n\n" +
    "💰 MNW Coin System:\n" +
    "• Base: 1 coin per 10 points\n" +
    "• High Score Bonus: 10x base coins\n" +
    "• Leader Bonus: 25x base coins\n\n" +
    "📈 Example: 100 points = 10 base coins\n" +
    "If it's your new high score: +100 bonus\n" +
    "If you're the leader: +250 bonus\n" +
    "Total: 360 coins!\n\n" +
    "📊 Leaderboard\n" +
    "Use the `/leaderboard` command to see\n\n" +
    "the top players.\n\n" +
    "📢 Remember\n\n" + "Every point is a step for peace!\n\n" +
    "Start your mission now!";

    this.add.text(vars.w/2, vars.h*0.17, msg, { font: `${vars.fontSmall+3}px monospace`, fill: "#fff", align: "center" }).setOrigin(0.5,0);
    this.add.text(vars.w/2, vars.h - 80, "< Back", { font: `${vars.fontMid}px monospace`, fill: "#67f" })
      .setOrigin(0.5)
      .setInteractive()
      .on('pointerup', () => this.scene.start('LobbyScene'));
 
  }
}

class LeaderboardScene extends Phaser.Scene {
  constructor() { super('LeaderboardScene'); }
  async create() {
    const vars = getScaleVars(this);
    this.add.rectangle(vars.w/2, vars.h/2, vars.w, vars.h, 0x000000, 0.93);
    this.add.text(vars.w/2, vars.h*0.11, "Leaderboard", { font: `${vars.fontBig}px monospace`, fill: "#ffe349" }).setOrigin(0.5,0);

    const leaders = await fetchLeaderboard();
    let y = vars.h*0.17;
    leaders.forEach((u, i) => {
      this.add.text(vars.w/2, y + i * (vars.fontSmall+16), `${i + 1}. ${u.username || "Anon"} - ${u.total_score} pts`, { font: `${vars.fontSmall+4}px monospace`, fill: "#fff" }).setOrigin(0.5,0);
    });

    this.add.text(vars.w/2, vars.h - 80, "< Back", { font: `${vars.fontMid}px monospace`, fill: "#67f" })
      .setOrigin(0.5)
      .setInteractive()
      .on('pointerup', () => this.scene.start('LobbyScene'));
  }
}

function showSmoke(scene, x, y) {
   let smoke = scene.add.image(x, y, 'destroyed_building').setScale(0.17).setAlpha(0.93);
    scene.tweens.add({
        targets: smoke,
        y: y - 25,
        scale: 0.23,
        alpha: 0,
        duration: 1700,
        onComplete: () => smoke.destroy()
    });
}


async function sendScoreToBot(score) {
    console.log("=== sendScoreToBot başladı ===");
    console.log("Gönderilecek skor:", score);
    console.log("Mevcut kullanıcı:", currentUser);
    
    if (!currentUser || !currentUser.id) {
        console.log("Kullanıcı bilgisi bulunamadı, skor kaydedilemedi");
        return;
    }
    
    try {
        // Bot URL'ini belirle - production'da Google Cloud Run URL'i kullan
        const isLocalhost = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
        const botUrl = isLocalhost 
            ? 'http://localhost:5000/save_score' 
            : 'https://peacebot-641906716058.europe-central2.run.app/save_score';
        
        console.log("Bot URL'ine istek gönderiliyor:", botUrl);
        
        const response = await fetch(botUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                user_id: currentUser.id,
                score: score
            })
        });
        
        if (response.ok) {
            const result = await response.json();
            console.log("Skor başarıyla kaydedildi:", result);
            
            // Bonus mesajını göster
            if (result.bonus_message) {
                console.log("Bonus mesajı:", result.bonus_message);
                // Bonus mesajını oyuncuya göster
                showBonusMessage(result.bonus_message);
            }
            
            // Kullanıcı verilerini güncelle
            userStats = {
                score: result.new_score,
                total_score: result.new_total_score,
                total_pmno_coins: result.new_total_coins,
                username: currentUser.username || "Player"
            };
            
            console.log("Kullanıcı verileri güncellendi:", userStats);
        } else {
            const error = await response.json();
            console.error("Skor kaydedilirken hata:", error);
        }
        
    } catch (error) {
        console.error("Skor gönderme hatası:", error);
    }
    
    console.log("=== sendScoreToBot bitti ===");
}

// Bonus mesajını göster
function showBonusMessage(message) {
    // GameOverScene'de bonus mesajını göster
    const gameOverScene = game.scene.getScene('GameOverScene');
    if (gameOverScene) {
        const vars = getScaleVars(gameOverScene);
        const bonusText = gameOverScene.add.text(
            vars.w/2, 
            vars.h*0.5, 
            message, 
            { 
                font: '18px monospace', 
                color: "#ffd700",
                backgroundColor: "#1a1a1ac9",
                align: "center",
                padding: { left: 10, right: 10, top: 5, bottom: 5 }
            }
        ).setOrigin(0.5);
        
        // 5 saniye sonra sil
        gameOverScene.time.delayedCall(5000, () => {
            bonusText.destroy();
        });
    }
}

// Hata mesajını göster
function showErrorMessage(message) {
    const currentScene = game.scene.getScene(game.scene.getActiveScene());
    if (currentScene) {
        const vars = getScaleVars(currentScene);
        const errorText = currentScene.add.text(
            vars.w/2, 
            vars.h*0.3, 
            message, 
            { 
                font: '20px monospace', 
                color: "#ff4444",
                backgroundColor: "#1a1a1a",
                align: "center",
                padding: { left: 15, right: 15, top: 10, bottom: 10 }
            }
        ).setOrigin(0.5);
        
        // 10 saniye sonra sil
        currentScene.time.delayedCall(10000, () => {
            errorText.destroy();
        });
    }
}





// --- Phaser Başlat ---
const gameWidth = window.innerWidth;
const gameHeight = window.innerHeight;
const config = {
    type: Phaser.AUTO,
    parent: 'phaser-game',
    width: gameWidth,
    height: gameHeight,
    backgroundColor: "#000",
    scene: [BootScene, LobbyScene, SideSelectScene, GameScene, GameOverScene, HowToPlayScene, LeaderboardScene],
    physics: { default: "arcade", arcade: { gravity: { y: 0 } } },
    scale: { mode: Phaser.Scale.FIT, autoCenter: Phaser.Scale.CENTER_BOTH }
};

const game = new Phaser.Game(config);
