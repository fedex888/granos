import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:go_router/go_router.dart';

const String kAlertTopic = 'alertas-granos';
const String kChannelId = 'alertas-granos';
const String kChannelName = 'Alertas de granos';

/// Handler de mensajes en background/terminado (debe ser top-level).
@pragma('vm:entry-point')
Future<void> firebaseBackgroundHandler(RemoteMessage message) async {
  await Firebase.initializeApp();
}

/// Inicializa FCM: permisos, topic, notificaciones locales y navegación al tocar.
class PushService {
  final GoRouter router;
  final FlutterLocalNotificationsPlugin _local = FlutterLocalNotificationsPlugin();

  PushService(this.router);

  Future<void> init() async {
    await Firebase.initializeApp();
    FirebaseMessaging.onBackgroundMessage(firebaseBackgroundHandler);

    const androidSettings = AndroidInitializationSettings('@mipmap/ic_launcher');
    await _local.initialize(
      settings: const InitializationSettings(android: androidSettings),
      onDidReceiveNotificationResponse: (response) => _handleTap(response.payload),
    );
    await _createChannel();

    final messaging = FirebaseMessaging.instance;
    await messaging.requestPermission(alert: true, badge: true, sound: true);
    await messaging.subscribeToTopic(kAlertTopic);

    // App en foreground: mostrar notificación local con el mismo contenido.
    FirebaseMessaging.onMessage.listen(_showForeground);

    // Tap con la app en background.
    FirebaseMessaging.onMessageOpenedApp.listen(
      (message) => _handleTap(message.data['product_id']?.toString()),
    );

    // Tap con la app cerrada.
    final initial = await messaging.getInitialMessage();
    if (initial != null) {
      _handleTap(initial.data['product_id']?.toString());
    }
  }

  Future<void> _createChannel() async {
    const channel = AndroidNotificationChannel(
      kChannelId,
      kChannelName,
      description: 'Oportunidades de compra y venta de granos',
      importance: Importance.high,
    );
    await _local
        .resolvePlatformSpecificImplementation<AndroidFlutterLocalNotificationsPlugin>()
        ?.createNotificationChannel(channel);
  }

  Future<void> _showForeground(RemoteMessage message) async {
    final notification = message.notification;
    if (notification == null) return;
    await _local.show(
      id: notification.hashCode,
      title: notification.title,
      body: notification.body,
      notificationDetails: const NotificationDetails(
        android: AndroidNotificationDetails(
          kChannelId,
          kChannelName,
          importance: Importance.high,
          priority: Priority.high,
        ),
      ),
      payload: message.data['product_id']?.toString(),
    );
  }

  void _handleTap(String? productId) {
    if (productId == null || productId.isEmpty) return;
    WidgetsBinding.instance.addPostFrameCallback((_) {
      router.go('/product/$productId');
    });
  }
}
