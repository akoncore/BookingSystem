import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.scss'],
})
export class HomeComponent {
  isLoggedIn = false; // auth сервисиңиз менен алмаштырыңыз

  services = [
    {
      title: 'Стрижки и укладки',
      description: 'Модные стрижки, профессиональные укладки и окрашивание волос',
      price: 'от 1 500 ₽',
      icon: 'scissors',
      color: 'pink',
      image: 'https://images.unsplash.com/photo-1563798163029-5448a0ffd596?w=600&q=80',
    },
    {
      title: 'Маникюр и педикюр',
      description: 'Классический и аппаратный маникюр, педикюр, дизайн ногтей',
      price: 'от 1 200 ₽',
      icon: 'sparkles',
      color: 'purple',
      image: 'https://images.unsplash.com/photo-1727199433272-70fdb94c8430?w=600&q=80',
    },
    {
      title: 'СПА процедуры',
      description: 'Массаж, уход за кожей лица и тела, релаксирующие процедуры',
      price: 'от 2 000 ₽',
      icon: 'star',
      color: 'indigo',
      image: 'https://images.unsplash.com/photo-1745327883508-b6cd32e5dde5?w=600&q=80',
    },
  ];

  stats = [
    { value: '500+', label: 'Довольных клиентов' },
    { value: '15+',  label: 'Лет опыта' },
    { value: '4.9',  label: 'Рейтинг' },
  ];

  footerLinks = [
    { label: 'Стрижки',    href: '#' },
    { label: 'Окрашивание', href: '#' },
    { label: 'Маникюр',    href: '#' },
    { label: 'СПА',        href: '#' },
  ];
}