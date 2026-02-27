import { Routes } from '@angular/router';
import { Login } from './component/login/login';
import path from 'path';
import { HomeComponent } from './pages/home/home.component';

export const routes: Routes = [
    {path:'',component:HomeComponent}
];
